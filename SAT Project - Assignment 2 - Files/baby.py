"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple

class ImplicationGraph:
    # graph is used in CDCL to track which assignments/clauses lead to which assignments of variable
    #this way we can locate where we 'went wrong' and learn from our mistakes! simply said :)
    # tracks which assignments caused whcih asignments. 
    def __init__(self):
        #creates a graph where the nodes are the variables with their assignemtns, with edges that point toward
        #the variables which they forced to be assigned
        self.nodes = {}     # Variable either False or True
        self.edges = {}     # List of variables that caused it to be assigend True or False
        self.reasons = {}   # List of Clauses that caused the assignment
        self.conflict_clause = None # The clause that results in a conflict

    def add_assignment(self, var, value, reason=None, implied_by=None):
        #ads an assignemnt to graph
        self.nodes[var] = value
        if implied_by:
            self.edges[var] = implied_by
        else:
            self.edges[var] = []
        if reason:
            self.reasons[var] = reason

    def add_conflict(self, clause):
        #register conflict
        self.conflict_clause = clause

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

def remove_tautologies(clauses):
    cleaned_clauses = []
    for clause in clauses:
        literals = set(clause)
        if any(-lit in literals for lit in literals):
            continue
        cleaned_clauses.append(list(literals))
    return cleaned_clauses

def choose_variable(clauses):
    # NO HEURISTIC, just pick the first literal of the first clause
    return abs(clauses[0][0])

def analyze_conflict(graph, level, current_level):
    conflict_clause = graph.conflict_clause[:]  # make a copy
    learned_clause = conflict_clause[:]
    
    # Count how many literals in this clause are at the current level
    count_current_level = 0  # start with 0

    for lit in learned_clause:
        var = abs(lit)  # get the variable number, ignoring the sign
        var_level = level.get(var, -1)  # get the decision level, default to -1 if not assigned
        if var_level == current_level:
            count_current_level += 1  # increment if this literal is at the current decision level

    
    return learned_clause, count_current_level

def resolve_clause(graph, level, current_level, learned_clause):
    while True:
        # Count literals at current level
        current_level_lits = [lit for lit in learned_clause if level.get(abs(lit), -1) == current_level]
        
        if len(current_level_lits) <= 1:
            break  # first UIP reached
        
        # Pick the last assigned literal at current level (heuristic)
        pivot = current_level_lits[-1]
        reason_clause = graph.reasons.get(abs(pivot))
        
        if not reason_clause:
            break  # decision literal, can't resolve further
        
        # Resolve: remove pivot, add all literals from reason clause except -pivot
        learned_clause = [lit for lit in learned_clause if lit != pivot] + [lit for lit in reason_clause if lit != -pivot]
    
    return list(set(learned_clause))  # remove duplicates

def get_backtrack_level(learned_clause, level, current_level):
    levels = [level.get(abs(lit), 0) for lit in learned_clause if level.get(abs(lit), 0) != current_level]
    return max(levels) if levels else 0


def dpll_cdcl(clauses, assignment, graph, level, current_level):
    """
    CDCL SAT solver.
    """
    print(len(clauses))
    while True:
        # --- Unit propagation ---
        unit_found = True
        while unit_found:
            unit_found = False
            for lit, reason_clause in (find_unit_clause(clauses, assignment) or []):
                var = abs(lit)
                if var in assignment:
                    continue
                val = lit > 0
                assignment[var] = val
                level[var] = current_level
                graph.add_assignment(var, val, reason=reason_clause)
                unit_found = True
            clauses = simplify(clauses, assignment)

        # --- Check for conflicts ---
        conflict_clause = None
        for c in clauses:
            if len(c) == 0:
                conflict_clause = c
                print("conflict_clause:", conflict_clause)
                break
            
        print("conflict_clause:", conflict_clause)
        if conflict_clause:
            print("CONFLICTTTT CLAUSEEE ")
            # Conflict found → CDCL backtracking
            graph.add_conflict(conflict_clause)
            learned_clause, _ = analyze_conflict(graph, level, current_level)
            learned_clause = resolve_clause(graph, level, current_level, learned_clause)
            backtrack_level = get_backtrack_level(learned_clause, level, current_level)
            clauses.append(learned_clause)

            # Undo assignments above backtrack_level
            for var in list(assignment.keys()):
                if level.get(var, 0) > backtrack_level:
                    assignment.pop(var)
                    level.pop(var, None)
                    graph.nodes.pop(var, None)
                    graph.reasons.pop(var, None)

            current_level = backtrack_level
            if current_level < 0:
                return False
            continue  # retry after backtracking

        # --- Check if solved ---
        if not clauses:
            return True

        # --- Pure literal elimination ---
        pure = find_pure_literal(clauses)
        if pure is not None:
            print("pure")
            var = abs(pure)
            val = pure > 0
            assignment[var] = val
            graph.add_assignment(var, val, reason="pure literal")
            continue


        # --- Check if solved ---
        if not clauses:
            return True

        # --- Decision branching ---
        # Only pick variable if there are non-empty clauses
        non_empty_clauses = [c for c in clauses if c]
        if not non_empty_clauses:
            # No clauses left to branch on, must be SAT
            return True
        var = choose_variable(non_empty_clauses)

        # --- Decision branching ---
        for val in [True, False]:
            print("branch")
            new_assignment = assignment.copy()
            new_assignment[var] = val
            new_level = current_level + 1
            level[var] = new_level
            graph.add_assignment(var, val, reason="decision")
            simplified_clauses = simplify(clauses, new_assignment)
            if dpll_cdcl(simplified_clauses, new_assignment, graph, level, new_level):
                assignment.update(new_assignment)
                return True
        return False  # both branches fail



def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    """
    Implement your SAT solver here.
    Must return:
      ("SAT", model)  where model is a list of ints (DIMACS-style), or
      ("UNSAT", None)
    """
    graph = ImplicationGraph()
    level = {}            # NEW: store decision level for each variable
    current_level = 0 

    assignment = {}
    result = dpll_cdcl(clauses, assignment, graph, level, current_level)
    if result:
        model = [v if assignment.get(v, False) else -v for v in range(1, num_vars + 1)] # unreasonable line\
        return ("SAT", model)
    else:
        return ("UNSAT"), None
    



    
