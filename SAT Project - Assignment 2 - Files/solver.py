"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple


def simplify(clauses, assignment):
    "With the current assignment, simplify the clauses."
    new_clauses = []
    for clause in clauses:
        # Skip satidsfied clauses
        if any((lit > 0 and assignment.get(lit, None)==True) or
                (lit < 0 and assignment.get(-lit, None)==False ) for lit in clause):
            ### ERROR AT HERE
            continue
        # Remove falsified literals
        new_clause = [lit for lit in clause if not(
            (lit > 0 and assignment.get(lit, None)==False) or
            (lit < 0 and assignment.get(-lit, None)==True))]
        new_clauses.append(new_clause)


    return new_clauses


def find_unit_clause(clauses):
    for clause in clauses:
        if len(clause) == 1:
            return clause[0]
    return None

def find_pure_literal(clauses):
    all_literals = {lit for clause in clauses for lit in clause}
    for lit in all_literals:
        if -lit not in all_literals:
            return lit
    return None

def remove_tautologies(clauses):
    """Remove any clause that contains both x and -x"""
    cleaned_clauses = []
    for clause in clauses:
        literals = set(clause)
        if any(-lit in literals for lit in literals):
            continue
        cleaned_clauses.append(list(literals))
    return cleaned_clauses

def choose_variable(clauses):
    # Jeroslow-Wang Heuristic
    if not clauses:
        return 1

    # Track j_plus and j_minus scores for each literal
    j_plus = {}  # Score if the literal is True
    j_minus = {} # Score if the literal is False

    for clause in clauses:
        clen = len(clause)
        if clen == 0:
            continue

        clause_weight = 1.0 / (1 << clen)

        for lit in clause:
            # For each literal, calculate the score if it is made True
            if lit > 0:
                j_plus[lit] = j_plus.get(lit, 0.0) + clause_weight
            else:
                j_minus[-lit] = j_minus.get(-lit, 0.0) + clause_weight

    if not j_plus and not j_minus:
        return abs(clauses[0][0])

    # Find literal with maximum j = max(j_plus, j_minus)
    best_literal = None
    best_score = -1.0

    # Check all positive literals
    for lit, score in j_plus.items():
        if score > best_score:
            best_score = score
            best_literal = lit

    # Check all negative literals
    for var, score in j_minus.items():
        lit = -var  # Convert to negative literal
        if score > best_score:
            best_score = score
            best_literal = lit

    return abs(best_literal)


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
    



    
