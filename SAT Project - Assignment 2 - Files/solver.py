"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple


def simplify(clauses, assignment):
    pass

def find_unit_clause(clauses):
    pass

def find_pure_literal(clauses):
    pass

def remove_tautologies(clauses):
    pass

def choose_variable(clauses):
    pass


def dpll(clauses: Iterable[Iterable[int]], assignment: dict) -> Tuple[str, List[int] | None]:
    """
    DPLL SAT Solver implementation.
    Parameters:
      clauses: Iterable of clauses, each clause is an iterable of integers (literals).
      assignment: Current variable assignment as a dictionary {var: bool}.
    Returns:
      True if satisfiable with the current assignment, False otherwise.
    """
    clauses = simplify(clauses, assignment) # Simplify clauses based on current assignment

    # -- Remove any tautological clauses --
    clauses = remove_tautologies(clauses)

    # -- Base cases --
    if not clauses:
        return True # All clauses satisfied
    if any(not clause for clause in clauses):
        return False # Found an empty clause, unsatisfiable

    # -- Implement unit propagation -- 
    unit = find_unit_clause(clauses)
    if unit is not None:
        var = abs(unit)
        value = unit > 0
        assignment[var] = value
        return dpll(clauses, assignment)
    
    # -- Pure literal elimination --
    pure = find_pure_literal(clauses)
    if pure is not None:
        var=abs(pure)
        value = pure > 0
        assignment[var] = value 
        return dpll(clauses, assignment)
    
    # -- Branching and Back tracking --
    ## FOR NOW, we use a simple heuristic to choose the next variable to assign.
    var = choose_variable(clauses) ## HEURISTIC CAN BE MODIFIED HERE

    for val in [True, False]:
        
        new_assignment = assignment.copy()
        assignment[abs(var)] = val

        if dpll(clauses, new_assignment):
            assignment.update(new_assignment)
            return True
    return False




    



    # Choose a variable to assign (simple heuristic: first literal of the first clause)
    ######## YOUR HEURISTIC HERE ########



def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Implement your SAT solver here.
    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """

    assignment = {}
    result = dpll(clauses, assignment)
    if result:
        model = [v if assignment.get(v, False) else -v for v in range(1, num_vars + 1)] # unreasonable line\
        print(model)
        return ("SAT", model)
    else:
        return ("UNSAT"), None
    



    
