"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple


def simplify(clauses, assignment):
    "With the current assignment, simplify the clauses."
    i = 0
    while i < len(clauses):
        clause = clauses[i]
        j = 0
        clause_satisfied = False

        while j < len(clause):
            lit = clause[j]
            var = abs(lit)
            assign_val = assignment.get(var)

            if assign_val is not None:
                if (lit > 0 and assign_val) or (lit < 0 and not assign_val):
                    clause_satisfied = True
                    break
                else:
                    # Remove falsified literals
                    clause.pop(j)
                    continue  # Skip incrementing j
            j += 1

        if clause_satisfied:
            # Remove satisfied clauses
            clauses.pop(i)
        elif not clause:  # Empty clause - UNSAT
            return None
        else:
            i += 1

    return clauses


def find_unit_clause(clauses):
    for clause in clauses:
        if len(clause) == 1:
            return clause[0]
    return None

def find_pure_literal(clauses):
    seen_pos = set()
    seen_neg = set()

    for clause in clauses:
        for lit in clause:
            if lit > 0:
                seen_pos.add(lit)
            else:
                seen_neg.add(lit)

    # Find literals that appear only positively or only negatively
    for lit in seen_pos:
        if -lit not in seen_neg:
            return lit
    for lit in seen_neg:
        if -lit not in seen_pos:
            return lit
    return None

def remove_tautologies(clauses):
    """Remove any clause that contains both x and -x"""
    i = 0
    while i < len(clauses):
        clause = clauses[i]
        literals = set()
        has_tautology = False

        for lit in clause:
            if -lit in literals:
                has_tautology = True
                break
            literals.add(lit)

        if has_tautology:
            clauses.pop(i)
        else:
            i += 1

    return clauses

def choose_variable(clauses):
    # NO HEURISTIC, just pick the first literal of the first clause
    return abs(clauses[0][0])


def dpll(clauses: Iterable[Iterable[int]], assignment: dict) -> Tuple[str, List[int] | None]:
    """
    DPLL SAT Solver implementation.
    Parameters:
      clauses: Iterable of clauses, each clause is an iterable of integers (literals).
      assignment: Current variable assignment as a dictionary {var: bool}.
    Returns:
      True if satisfiable with the current assignment, False otherwise.
    """
    if not isinstance(clauses, list):
        clauses = [list(c) for c in clauses]

    clauses = simplify(clauses, assignment) # Simplify clauses based on current assignment

    if clauses is None:  # Conflict detected
        return False

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
        # Check for conflicts
        if var in assignment and assignment[var] != value:
            return False
        assignment[var] = value
        result = dpll(clauses, assignment)
        if not result:
            del assignment[var]  # Backtrack
        return result

    # -- Pure literal elimination --
    pure = find_pure_literal(clauses)
    if pure is not None:
        var=abs(pure)
        value = pure > 0
        if var in assignment and assignment[var] != value:
            return False

        assignment[var] = value
        result =  dpll(clauses, assignment)
        if not result:
            del assignment[var]  # Backtrack
        return result

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
    clauses_list = [list(clause) for clause in clauses]
    clauses_list = remove_tautologies(clauses_list)

    assignment = {}
    result = dpll(clauses_list, assignment)
    if result:
        model = [v if assignment.get(v, False) else -v for v in range(1, num_vars + 1)] # unreasonable line\
        print(model)
        return ("SAT", model)
    else:
        return ("UNSAT"), None
    



    
