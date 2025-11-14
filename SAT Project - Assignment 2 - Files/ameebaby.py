#!/usr/bin/env python3
"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)
"""

from typing import Iterable, List, Tuple

# ------------------------------
# Basic helpers for literals
# ------------------------------

def var_of(lit: int) -> int:
    """Get variable index from literal (1-based)."""
    return abs(lit)

def neg(lit: int) -> int:
    """Negate a literal."""
    return -lit


# ------------------------------
# CDCL Solver
# ------------------------------

class CDCLSolver:
    def __init__(self, clauses: List[List[int]], num_vars: int):
        self.num_vars = num_vars

        # Clause database: original clauses + learned clauses
        self.clauses: List[List[int]] = [list(c) for c in clauses]

        # Assignments: None = UNDEF, True/False = value
        # Use 1-based indexing for variables (index 0 unused)
        self.assigns: List[bool | None] = [None] * (num_vars + 1)

        # Decision level per variable (0..current_level)
        self.level: List[int] = [0] * (num_vars + 1)

        # Reason clause per variable (None if decision)
        self.reason: List[List[int] | None] = [None] * (num_vars + 1)

        # Trail of assigned literals in order
        self.trail: List[int] = []

        # trail_lim[i] = index in trail where decision level i starts
        self.trail_lim: List[int] = []

    # ------------------------------
    # Utility methods
    # ------------------------------

    def current_level(self) -> int:
        return len(self.trail_lim)

    def value_lit(self, lit: int) -> bool | None:
        """
        Evaluate literal under current assignment:
          - True  if clause satisfied by this literal
          - False if this literal is falsified
          - None  if var is unassigned
        """
        v = var_of(lit)
        val = self.assigns[v]
        if val is None:
            return None
        # literal positive and var True OR literal negative and var False
        if (lit > 0 and val is True) or (lit < 0 and val is False):
            return True
        else:
            return False

    def new_decision_level(self) -> None:
        self.trail_lim.append(len(self.trail))

    def enqueue(self, lit: int, reason: List[int] | None) -> bool:
        """
        Assign literal lit with given reason clause.
        Returns False if this contradicts an existing assignment.
        """
        v = var_of(lit)
        val = (lit > 0)
        cur = self.assigns[v]
        if cur is not None:
            # Check for consistency
            return cur == val

        self.assigns[v] = val
        self.level[v] = self.current_level()
        self.reason[v] = reason
        self.trail.append(lit)
        return True

    # ------------------------------
    # Propagation
    # ------------------------------

    def propagate(self) -> List[int] | None:
        """
        Naive unit propagation:
          - returns conflict clause if a conflict is found
          - returns None otherwise
        """
        # We propagate until no new assignments are made
        while True:
            any_new = False

            for clause in self.clauses:
                # Check clause status: satisfied / unit / conflict / unresolved
                num_unassigned = 0
                last_unassigned = None
                clause_sat = False

                for lit in clause:
                    val = self.value_lit(lit)
                    if val is True:
                        clause_sat = True
                        break
                    elif val is None:
                        num_unassigned += 1
                        last_unassigned = lit

                if clause_sat:
                    continue

                if num_unassigned == 0:
                    # All literals are False -> conflict
                    return clause

                if num_unassigned == 1 and last_unassigned is not None:
                    # Unit clause -> force the last unassigned literal
                    if not self.enqueue(last_unassigned, clause):
                        # Contradiction when enqueuing
                        return clause
                    any_new = True

            if not any_new:
                break

        return None

    # ------------------------------
    # Conflict Analysis (1-UIP)
    # ------------------------------

    def analyze(self, confl_clause: List[int]) -> Tuple[List[int], int]:
        """
        Perform 1-UIP conflict analysis.
        Returns (learned_clause, backtrack_level).
        """
        seen: set[int] = set()
        learnt: List[int] = []
        pathC = 0
        p = None  # last involved literal

        # Start from conflict clause
        c = confl_clause
        idx = len(self.trail) - 1  # start from end of trail

        while True:
            # walk the clause
            for lit in c:
                v = var_of(lit)
                if v not in seen and self.level[v] > 0:
                    seen.add(v)
                    if self.level[v] == self.current_level():
                        pathC += 1
                    else:
                        learnt.append(lit)

            # select the last assigned literal at current level in 'seen'
            while True:
                p = self.trail[idx]
                v = var_of(p)
                idx -= 1
                if v in seen:
                    break

            seen.remove(v)
            pathC -= 1
            reason_clause = self.reason[v]

            if pathC == 0:
                break

            if reason_clause is None:
                # no reason for this literal (decision) -> stop
                break

            # move to the reason clause of this literal
            c = reason_clause

        # asserting literal is negation of p
        assert p is not None
        learnt.append(neg(p))

        # compute backtrack level: max level among literals in learnt except the asserting one
        if len(learnt) == 1:
            backtrack_level = 0
        else:
            max_level = 0
            for lit in learnt[:-1]:
                v = var_of(lit)
                lv = self.level[v]
                if lv > max_level:
                    max_level = lv
            backtrack_level = max_level

        return learnt, backtrack_level

    # ------------------------------
    # Backtracking
    # ------------------------------

    def cancel_until(self, level: int) -> None:
        """
        Backtrack to a given decision level:
        unassign all variables with level > level.
        """
        if self.current_level() <= level:
            return

        # Index in trail where level+1 starts
        cut = self.trail_lim[level]
        # Unassign all variables from trail[cut:]
        for i in range(len(self.trail) - 1, cut - 1, -1):
            v = var_of(self.trail[i])
            self.assigns[v] = None
            self.reason[v] = None
            self.level[v] = 0

        self.trail = self.trail[:cut]
        self.trail_lim = self.trail_lim[:level]

    # ------------------------------
    # Branching heuristic
    # ------------------------------

    def pick_branch_lit(self) -> int | None:
        """
        Very simple branching: pick the smallest-index unassigned var, with positive polarity.
        """
        for v in range(1, self.num_vars + 1):
            if self.assigns[v] is None:
                return v  # literal "v" (positive)
        return None

    # ------------------------------
    # Main CDCL solve loop
    # ------------------------------

    def solve(self) -> bool:
        """
        Main CDCL search loop:
         - propagate
         - if conflict, analyze, learn, backjump
         - else, if all assigned -> SAT
         - else, decide a new variable
        """
        while True:
            confl = self.propagate()
            if confl is not None:
                # Conflict
                if self.current_level() == 0:
                    # Conflict at root level -> UNSAT
                    return False

                learnt, backtrack_level = self.analyze(confl)
                # Add learned clause
                self.clauses.append(learnt)
                # Backjump
                self.cancel_until(backtrack_level)
                # Enqueue the asserting literal of the learned clause
                asserting_lit = learnt[-1]  # last literal is neg(p)
                self.enqueue(asserting_lit, learnt)

            else:
                # No conflict: check if all variables are assigned
                all_assigned = True
                for v in range(1, self.num_vars + 1):
                    if self.assigns[v] is None:
                        all_assigned = False
                        break
                if all_assigned:
                    return True

                # Decide a new branching literal
                next_var = self.pick_branch_lit()
                if next_var is None:
                    # Nothing left to assign -> SAT
                    return True

                self.new_decision_level()
                decision_lit = next_var  # choose positive polarity
                self.enqueue(decision_lit, None)


# ------------------------------
# Top-level API for the assignment
# ------------------------------

def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Entry point for the SAT solver.

    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
    clause_list = [list(cl) for cl in clauses]

    solver = CDCLSolver(clause_list, num_vars)
    sat = solver.solve()

    if sat:
        # DIMACS model: for each v in 1..num_vars:
        #  - v  if variable v is True
        #  - -v if variable v is False or unassigned (default false)
        model: List[int] = []
        for v in range(1, num_vars + 1):
            val = solver.assigns[v]
            if val is True:
                model.append(v)
            else:
                model.append(-v)
        return "SAT", model
    else:
        return "UNSAT", None