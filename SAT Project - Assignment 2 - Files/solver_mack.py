"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""

import random
from typing import Iterable, List, Tuple
assign_average = []
# class ImplicationGraph:
#     # graph is used in CDCL to track which assignments/clauses lead to which assignments of variable
#     #this way we can locate where we 'went wrong' and learn from our mistakes! simply said :)
#     # tracks which assignments caused whcih asignments. 
#     def __init__(self):
#         #creates a graph where the nodes are the variables with their assignemtns, with edges that point toward
#         #the variables which they forced to be assigned
#         self.nodes = {}     # Variable either False or True
#         self.edges = {}     # List of variables that caused it to be assigend True or False
#         self.reasons = {}   # List of Clauses that caused the assignment
#         self.conflict_clause = None # The clause that results in a conflict

#     def add_assignment(self, var, value, reason=None, implied_by=None):
#         #ads an assignemnt to graph
#         self.nodes[var] = value
#         if implied_by:
#             self.edges[var] = implied_by
#         else:
#             self.edges[var] = []
#         if reason:
#             self.reasons[var] = reason

#     def add_conflict(self, clause):
#         #register conflict
#         self.conflict_clause = clause

def simplify(clauses, assignment):
    new_clauses = []
    for clause in clauses:
        # Clause is satisfied if any literal is True under assignment
        satisfied = False 
        for lit in clause:
            if lit > 0:  # positive literal 
                if assignment.get(lit, None) == True:
                    satisfied = True #if the positive literal is assigned true, the clause is satisfied 
                    break  

            else:  # negative literal
                if assignment.get(-lit, None) == False:
                    satisfied = True #same but otherway around for negative
                    break

        # Skip satidsfied clauses
        if satisfied:
            continue  

        new_clause = []

        for lit in clause:
            if lit > 0:
                # Positive literal
                if assignment.get(lit, None) != False:
                    # Keep it if it's not assigned False
                    new_clause.append(lit)
            else:
                # Negative literal
                var = -lit
                if assignment.get(var, None) != True:
                    # Keep it if its variable is not assigned True
                    new_clause.append(lit)

        # Add the processed clause to the list of new clauses
        new_clauses.append(new_clause)
    return new_clauses

def find_unit_clause(clauses, assignment):
    all_units = []
    for clause in clauses:
        unassigned = [lit for lit in clause if assignment.get(abs(lit), None) is None] #finds all unassigned literalls
        falses = [lit for lit in clause if (lit > 0 and assignment.get(lit, None) == False) or 
                  (lit < 0 and assignment.get(-lit, None) == True)] 
        if len(unassigned) == 1 and len(falses) == len(clause) - 1:
            # Only one unassigned literal → unit
            all_units.append((unassigned[0], clause[:]))  # return literal + clause
    return all_units if all_units else None

def find_pure_literal(clauses):
    all_literals = {lit for clause in clauses for lit in clause}
    for lit in all_literals:
        if -lit not in all_literals:
            return lit
    return None

def choose_variable(clauses):
    # Return a random literal from the first clause
    return abs(random.choice(clauses[0]))


def dpll(clauses, assignment, graph, level, current_level, clauses_copy):
    """
    CDCL-style DPLL SAT solver.
    Returns True if SAT, False if UNSAT.
    """
    global assign_average

    # assigned = 0
    # for i in assignment:
    #     if assignment.get(i, None) != None:
    #         assigned += 1
    # assign_average.append(assigned)
    # assigned = 0
    # if len (assign_average[-10:]) > 9:
    #     assign_average = [i for i in assign_average if i != 0]
    #     if max(assign_average[-10:]) - min(assign_average[-10:]) < 11:
    #         print(max(assign_average[-15:]) - min(assign_average[-15:]))
    #         for key in assignment.keys():
    #             current_level = 0
    #             assignment[key] = None
    #             clauses = clauses_copy
    #             assign_average = []
    while True:
        # --- Full unit propagation ---
        unit_found = False
        for lit, reason_clause in (find_unit_clause(clauses, assignment) or []):
            var = abs(lit)
            value = lit > 0
            if var in assignment:
                continue
            assignment[var] = value
            level[var] = current_level
            # graph.add_assignment(var, value, reason=reason_clause)
            unit_found = True
        if not unit_found:
            break  # no more units to propagate
        clauses = simplify(clauses, assignment)

    # --- Check for empty clause (conflict) ---
    for clause in clauses:
        if len(clause) == 0:
            return False  # will retry after backtracking

    # --- Base case: all clauses satisfied ---
    if not clauses:
        return True

    # --- Pure literal elimination ---
    pure = find_pure_literal(clauses)
    if pure is not None:
        var = abs(pure)
        value = pure > 0
        assignment[var] = value
        # graph.add_assignment(var, value, reason="pure literal")
        return dpll(clauses, assignment, graph, level, current_level, clauses_copy)

    # --- Decision branching ---
    var = choose_variable(clauses)
    for val in [True, False]:
        new_assignment = assignment.copy()
        new_assignment[var] = val
        new_level = current_level + 1
        level[var] = new_level
        # graph.add_assignment(var, val, reason="decision")
        simplified_clauses = simplify(clauses, new_assignment)
        if dpll(simplified_clauses, new_assignment, graph, level, new_level, clauses_copy):
            assignment.update(new_assignment)
            return True

    # If both branches fail, return UNSAT
    return False

def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Implement your SAT solver here.
    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
    # graph = ImplicationGraph()
    graph = {}
    level = {}            # NEW: store decision level for each variable
    current_level = 0 
    clauses_copy = clauses.copy()
    assignment = {}

    result = dpll(clauses, assignment, graph, level, current_level, clauses_copy)
    if result:
        model = [v if assignment.get(v, False) else -v for v in range(1, num_vars + 1)] # unreasonable line\
        return ("SAT", model)
    else:
        return ("UNSAT"), None





