#!/usr/bin/env python3
"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)
"""

from typing import Iterable, List, Tuple, Dict


class ImplicationGraph:
    # Graph is used (conceptually) in CDCL to track which assignments/clauses
    # lead to which assignments of a variable.
    def __init__(self):
        # var -> True/False
        self.nodes: Dict[int, bool] = {}
        # var -> list of vars that implied it (not heavily used here)
        self.edges: Dict[int, List[int]] = {}
        # var -> clause that caused assignment (reason)
        self.reasons: Dict[int, List[int]] = {}
        # The clause that resulted in a conflict
        self.conflict_clause: List[int] | None = None

    def add_assignment(self, var, value, reason=None, implied_by=None):
        # Add an assignment to the graph
        self.nodes[var] = value
        if implied_by:
            self.edges[var] = implied_by
        else:
            self.edges[var] = []
        if reason is not None:
            self.reasons[var] = reason

    def add_conflict(self, clause):
        # Register conflict clause
        self.conflict_clause = clause


def simplify(clauses, assignment):
    """
    Simplify a CNF formula under a partial assignment:
      - Drop satisfied clauses
      - Remove falsified literals from remaining clauses
    """
    new_clauses = []
    for clause in clauses:
        # Clause is satisfied if any literal is True under assignment
        satisfied = False
        for lit in clause:
            if lit > 0:  # positive literal
                if assignment.get(lit, None) is True:
                    satisfied = True
                    break
            else:  # negative literal
                if assignment.get(-lit, None) is False:
                    satisfied = True
                    break

        # Skip satisfied clauses
        if satisfied:
            continue

        new_clause = []
        for lit in clause:
            if lit > 0:
                # Positive literal: keep if not assigned False
                if assignment.get(lit, None) is not False:
                    new_clause.append(lit)
            else:
                # Negative literal: keep if variable not assigned True
                var = -lit
                if assignment.get(var, None) is not True:
                    new_clause.append(lit)

        new_clauses.append(new_clause)
    return new_clauses


def find_unit_clause(clauses, assignment):
    """
    Return list of (unit_literal, clause) for all unit clauses, or None if none.
    A clause is unit if exactly one literal is unassigned and all others are false.
    """
    all_units = []
    for clause in clauses:
        unassigned = [lit for lit in clause if assignment.get(abs(lit), None) is None]
        falses = [
            lit
            for lit in clause
            if (lit > 0 and assignment.get(lit, None) is False)
            or (lit < 0 and assignment.get(-lit, None) is True)
        ]
        if len(unassigned) == 1 and len(falses) == len(clause) - 1:
            all_units.append((unassigned[0], clause[:]))  # literal + reason clause
    return all_units if all_units else None


def find_pure_literal(clauses):
    """
    Find a pure literal (appears only with one polarity) or None if none.
    """
    all_literals = {lit for clause in clauses for lit in clause}
    for lit in all_literals:
        if -lit not in all_literals:
            return lit
    return None


def remove_tautologies(clauses):
    """
    Remove tautological clauses (containing both x and -x).
    """
    cleaned_clauses = []
    for clause in clauses:
        literals = set(clause)
        if any(-lit in literals for lit in literals):
            continue
        cleaned_clauses.append(list(literals))
    return cleaned_clauses


def choose_variable(clauses):
    """
    Very simple branching heuristic: pick the variable of the first literal of the first clause.
    """
    return abs(clauses[0][0])


# --- Conflict-related helpers kept for completeness / future CDCL extensions ---


def analyze_conflict(graph, level, current_level):
    """
    Placeholder for conflict analysis; currently unused in the DPLL core.
    """
    if graph.conflict_clause is None:
        return [], 0
    conflict_clause = graph.conflict_clause[:]  # make a copy
    learned_clause = conflict_clause[:]

    count_current_level = 0
    for lit in learned_clause:
        var = abs(lit)
        var_level = level.get(var, -1)
        if var_level == current_level:
            count_current_level += 1

    return learned_clause, count_current_level


def resolve_clause(graph, level, current_level, learned_clause):
    """
    Placeholder: naive resolution loop; currently not used by the core solver.
    """
    while True:
        current_level_lits = [
            lit for lit in learned_clause if level.get(abs(lit), -1) == current_level
        ]
        if len(current_level_lits) <= 1:
            break  # first UIP reached (conceptually)
        pivot = current_level_lits[-1]
        reason_clause = graph.reasons.get(abs(pivot))
        if not reason_clause:
            break  # decision literal, can't resolve further
        learned_clause = [
            lit for lit in learned_clause if lit != pivot
        ] + [lit for lit in reason_clause if lit != -pivot]
    return list(set(learned_clause))


def get_backtrack_level(learned_clause, level, current_level):
    """
    Compute backtrack level for a learned clause (CDCL-style).
    Currently not used by the core solver.
    """
    levels = [
        level.get(abs(lit), 0)
        for lit in learned_clause
        if level.get(abs(lit), 0) != current_level
    ]
    return max(levels) if levels else 0


# --- Core solver: DPLL with unit propagation and pure literal elimination ---


def dpll_cdcl(clauses, assignment, graph, level, current_level):
    """
    DPLL-style SAT solver with:
      - unit propagation
      - pure literal elimination
      - recursive branching

    CDCL-related helpers (analyze_conflict, resolve_clause, etc.) are present
    but the core logic here is a clean, correct DPLL.
    """

    # First, simplify w.r.t. current assignment
    clauses = simplify(clauses, assignment)

    # If any clause is empty -> conflict
    for c in clauses:
        if len(c) == 0:
            graph.add_conflict(c)
            return False

    # If no clauses left -> all satisfied
    if not clauses:
        return True

    # --- Unit propagation loop ---
    while True:
        units = find_unit_clause(clauses, assignment)
        if not units:
            break

        changed = False
        for lit, reason_clause in units:
            var = abs(lit)
            val = (lit > 0)
            if var in assignment:
                # Check for inconsistency
                if assignment[var] != val:
                    graph.add_conflict(reason_clause)
                    return False
                continue
            assignment[var] = val
            level[var] = current_level
            graph.add_assignment(var, val, reason=reason_clause)
            changed = True

        if not changed:
            break

        # Re-simplify after unit assignments
        clauses = simplify(clauses, assignment)
        # Check for conflict or success
        for c in clauses:
            if len(c) == 0:
                graph.add_conflict(c)
                return False
        if not clauses:
            return True

    # --- Pure literal elimination loop ---
    while True:
        pure = find_pure_literal(clauses)
        if pure is None:
            break
        var = abs(pure)
        val = (pure > 0)
        if var in assignment:
            if assignment[var] != val:
                # Conflict: variable already assigned opposite
                return False
        else:
            assignment[var] = val
            level[var] = current_level
            graph.add_assignment(var, val, reason="pure literal")
        clauses = simplify(clauses, assignment)
        for c in clauses:
            if len(c) == 0:
                graph.add_conflict(c)
                return False
        if not clauses:
            return True

    # --- If no clauses, SAT ---
    if not clauses:
        return True

    # --- Choose branching variable ---
    non_empty_clauses = [c for c in clauses if c]
    if not non_empty_clauses:
        return True  # trivially SAT
    var = choose_variable(non_empty_clauses)

    # --- Branch: try var = True, then var = False ---
    for val in [True, False]:
        new_assignment = assignment.copy()
        new_level_map = level.copy()
        new_assignment[var] = val
        new_level = current_level + 1
        new_level_map[var] = new_level
        graph.add_assignment(var, val, reason="decision")
        if dpll_cdcl(clauses, new_assignment, graph, new_level_map, new_level):
            # Propagate successful model back up
            assignment.clear()
            assignment.update(new_assignment)
            level.clear()
            level.update(new_level_map)
            return True

    # Both branches failed -> UNSAT under current prefix
    return False


def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Entry point for the SAT solver.

    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
    # Make sure we have a concrete list of clauses
    clause_list = [list(cl) for cl in clauses]
    clause_list = remove_tautologies(clause_list)

    graph = ImplicationGraph()
    level: Dict[int, int] = {}
    current_level = 0
    assignment: Dict[int, bool] = {}

    result = dpll_cdcl(clause_list, assignment, graph, level, current_level)

    if result:
        # Build DIMACS-style model: for each v in 1..num_vars,
        # if v is assigned True -> v, else -v.
        model = [
            v if assignment.get(v, False) else -v
            for v in range(1, num_vars + 1)
        ]
        return "SAT", model
    else:
        return "UNSAT", None