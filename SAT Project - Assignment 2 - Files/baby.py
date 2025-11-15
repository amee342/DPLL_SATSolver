#!/usr/bin/env python3
"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

This file implements a CDCL (Conflict-Driven Clause Learning) SAT solver.
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
        # IF reason is None, it was a 'decision'
        self.reasons: Dict[int, List[int] | None] = {}
        # The clause that resulted in a conflict
        self.conflict_clause: List[int] | None = None

    def add_assignment(self, var, value, reason=None, implied_by=None):
        # Add an assignment to the graph
        self.nodes[var] = value
        if implied_by:
            self.edges[var] = implied_by
        else:
            self.edges[var] = []
        self.reasons[var] = reason

    def add_conflict(self, clause):
        # Register conflict clause
        self.conflict_clause = clause

    def clear_at_level(self, var_levels, level):
        """Clear all graph info for variables at or above 'level'."""
        vars_to_undo = [v for v, l in var_levels.items() if l >= level]
        for v in vars_to_undo:
            if v in self.nodes:
                del self.nodes[v]
            if v in self.edges:
                del self.edges[v]
            if v in self.reasons:
                del self.reasons[v]


# --- Core Helper Functions ---

def find_unit_clause(clauses, assignment):
    """
    Return list of (unit_literal, clause) for all unit clauses, or None if none.
    A clause is unit if exactly one literal is unassigned and all others are false.
    """
    all_units = []
    for clause in clauses:
        unassigned_lit = None
        num_falsified = 0
        is_satisfied = False

        for lit in clause:
            var = abs(lit)
            val = (lit > 0)
            
            if var not in assignment:
                if unassigned_lit is None:
                    unassigned_lit = lit
                else:
                    # More than one unassigned, not unit
                    unassigned_lit = None # Mark as "not unit"
                    break 
            elif assignment[var] == val:
                # Clause is satisfied, skip it
                is_satisfied = True
                break
            else:
                # Literal is falsified
                num_falsified += 1
        
        if is_satisfied or unassigned_lit is None:
            continue

        if num_falsified == len(clause) - 1:
            all_units.append((unassigned_lit, clause[:]))  # literal + reason clause
            
    return all_units if all_units else None


def find_pure_literal(clauses, assignment):
    """
    Find a pure literal (appears only with one polarity) among *unassigned* vars
    or None if none.
    """
    all_literals = set()
    unassigned_vars = {abs(lit) for cl in clauses for lit in cl if abs(lit) not in assignment}
    
    # Only consider literals from clauses that are not yet satisfied
    for clause in clauses:
        satisfied = False
        for lit in clause:
            if abs(lit) in assignment and assignment[abs(lit)] == (lit > 0):
                satisfied = True
                break
        if not satisfied:
            for lit in clause:
                if abs(lit) in unassigned_vars:
                    all_literals.add(lit)

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


def choose_unassigned_variable(assignment, num_vars):
    """
    Simple branching heuristic: pick the first unassigned variable.
    """
    for v in range(1, num_vars + 1):
        if v not in assignment:
            return v
    return None

def is_falsified(clause, assignment):
    """Check if a clause is fully falsified by the assignment."""
    for lit in clause:
        var = abs(lit)
        val = (lit > 0)
        if var not in assignment:
            return False # Unassigned, so not falsified
        if assignment[var] == val:
            return False # Satisfied, so not falsified
    return True # All literals are assigned and false


# --- CDCL Core Functions ---

def propagate_units(clauses, assignment, var_levels, graph, current_level):
    """
    Perform Boolean Constraint Propagation (BCP).
    Iteratively finds unit clauses and assigns them.
    Returns: A conflicting clause if one is found, else None.
    """
    print(len(clauses))
    while True:
        units = find_unit_clause(clauses, assignment)
        if not units:
            break # BCP is stable

        for lit, reason_clause in units:
            var = abs(lit)
            val = (lit > 0)
            
            if var in assignment:
                if assignment[var] != val:
                    # Conflict: tried to assign two different values
                    graph.add_conflict(reason_clause)
                    return reason_clause
                # else: already assigned this value, continue
            else:
                assignment[var] = val
                var_levels[var] = current_level
                graph.add_assignment(var, val, reason=reason_clause)
        
        # After propagating, we *must* check if we created a conflict
        # This is the slow part that 2-watched-literals would optimize
        for clause in clauses:
            if is_falsified(clause, assignment):
                graph.add_conflict(clause)
                return clause
                
    return None # No conflict


def resolve(c1: List[int], c2: List[int], pivot_var: int) -> List[int]:
    """Resolve two clauses on a pivot variable."""
    lits1 = {l for l in c1 if abs(l) != pivot_var}
    lits2 = {l for l in c2 if abs(l) != pivot_var}
    return list(lits1.union(lits2))


def analyze_conflict_1UIP(graph: ImplicationGraph, var_levels: Dict[int, int], current_level: int) -> Tuple[List[int], int]:
    """
    Analyze the conflict to find the 1UIP (First Unique Implication Point)
    and produce a learned clause and backtrack level.
    """
    print(current_level)
    if graph.conflict_clause is None:
        return [], -1

    learned_clause = graph.conflict_clause[:]
    
    # Vars at current level that are in the conflict
    current_level_lits = {abs(l) for l in learned_clause if var_levels.get(abs(l), -1) == current_level}

    while True:
        # Check how many lits are from the current level
        lits_at_level = [l for l in learned_clause if var_levels.get(abs(l), -1) == current_level]
        
        # Find the *decision* variable at this level
        decision_var = -1
        for v in current_level_lits:
            if graph.reasons.get(v) is None: # None reason == decision
                decision_var = v
                break

        # We stop (1UIP) when the decision variable is the *only* one
        # from the current level left in our learned clause.
        if len(lits_at_level) == 1 and abs(lits_at_level[0]) == decision_var:
            break
            
        # Find the *last* implied variable in the clause
        # We need to find a literal 'pivot' that was *implied* (not a decision)
        pivot = -1
        pivot_var = -1
        
        # Iterate backwards through assignments in the graph to find the last-assigned
        # variable that is in our conflict. This is a simple (but correct)
        # way to find the variable to resolve on.
        # A faster way would be to track assignment order.
        found = False
        for var in reversed(list(graph.nodes.keys())): # Relies on dict insertion order (Python 3.7+)
            if var in current_level_lits and graph.reasons.get(var) is not None:
                pivot_var = var
                found = True
                break
        
        if not found:
             # This can happen if the conflict only involves the decision variable
             # and literals from lower levels.
             break

        reason_clause = graph.reasons[pivot_var]
        learned_clause = resolve(learned_clause, reason_clause, pivot_var)
        
        # Update our set of vars at this level
        current_level_lits = {abs(l) for l in learned_clause if var_levels.get(abs(l), -1) == current_level}


    # --- Calculate Backtrack Level ---
    # The backtrack level is the *second highest* level in the learned clause.
    # The highest (1UIP) is 'current_level'.
    if not learned_clause:
        return [], -1 # Empty learned clause means UNSAT at root

    levels = [var_levels.get(abs(l), 0) for l in learned_clause if var_levels.get(abs(l), 0) != current_level]
    backtrack_level = max(levels) if levels else 0

    return learned_clause, backtrack_level


def undo_assignments(assignment, var_levels, graph, level):
    """Undo all assignments made at or above 'level'."""
    vars_to_undo = [v for v, l in var_levels.items() if l >= level]
    for v in vars_to_undo:
        if v in assignment:
            del assignment[v]
        if v in var_levels:
            del var_levels[v]
    graph.clear_at_level(var_levels, level)


# --- Main Solver Entry Point ---

def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Entry point for the CDCL SAT solver.

    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
    # --- Initialization ---
    all_clauses = remove_tautologies([list(cl) for cl in clauses])
    assignment: Dict[int, bool] = {}    # var -> True/False
    var_levels: Dict[int, int] = {}     # var -> decision level
    graph = ImplicationGraph()
    current_level = 0
    
    # --- Root-level propagation (Level 0) ---
    conflict_clause = propagate_units(all_clauses, assignment, var_levels, graph, 0)
    if conflict_clause:
        return "UNSAT", None # Conflict at level 0

    # --- Main CDCL Loop ---
    while True:
        # --- 1. Make a Decision ---
        var = choose_unassigned_variable(assignment, num_vars)
        
        if var is None:
            # All variables are assigned, no conflict
            model = [
                v if assignment.get(v, False) else -v
                for v in range(1, num_vars + 1)
            ]
            return "SAT", model

        current_level += 1
        val = False # Heuristic: branch on False first
        assignment[var] = val
        var_levels[var] = current_level
        graph.add_assignment(var, val, reason=None) # None reason == decision

        # --- 2. Propagate ---
        conflict_clause = None
        while True:
            conflict_clause = propagate_units(all_clauses, assignment, var_levels, graph, current_level)
            if conflict_clause is None:
                # No conflict, break to make another decision
                break
            
            # --- 3. Conflict Found: Analyze & Backtrack ---
            learned_clause, backtrack_level = analyze_conflict_1UIP(graph, var_levels, current_level)

            if backtrack_level < 0 or not learned_clause:
                # Conflict at root level
                return "UNSAT", None
            
            # Add learned clause
            all_clauses.append(learned_clause)
            
            # Backjump
            undo_assignments(assignment, var_levels, graph, backtrack_level + 1)
            current_level = backtrack_level
            
            # The learned clause is *guaranteed* to be a unit clause
            # at the backtrack_level. We add its assignment *here*
            # before looping back to propagate_units.
            
            # Find the single literal from the learned clause at the backtrack_level
            unit_lit = -1
            for lit in learned_clause:
                if var_levels.get(abs(lit), -1) == backtrack_level:
                    unit_lit = lit
                    break
            
            # If no literal, it's a unit at level 0
            if unit_lit == -1:
                 # This logic should be handled by the next propagate_units call
                 # after backtracking to level 0. Let's just let it propagate.
                 pass
            else:
                 # This should also be caught by the next propagate call,
                 # but we can do it here explicitly.
                 var, val = abs(unit_lit), (unit_lit > 0)
                 if var not in assignment: # Assign the 1UIP literal
                     assignment[var] = val
                     var_levels[var] = backtrack_level
                     graph.add_assignment(var, val, reason=learned_clause)

            # Loop back to propagate_units