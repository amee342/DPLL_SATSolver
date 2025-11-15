"""
SAT Assignment Part 1 - Non-consecutive Sudoku Encoder (Puzzle -> CNF)

THIS is the file to edit.

Implement: to_cnf(input_path) -> (clauses, num_vars)

You're required to use a variable mapping as follows:
    var(r,c,v) = r*N*N + c*N + v
where r,c are in range (0...N-1) and v in (1...N).

You must encode:
  (1) Exactly one value per cell
  (2) For each value v and each row r: exactly one column c has v
  (3) For each value v and each column c: exactly one row r has v
  (4) For each value v and each sqrt(N)×sqrt(N) box: exactly one cell has v
  (5) Non-consecutive: orthogonal neighbors cannot differ by 1
  (6) Clues: unit clauses for the given puzzle
"""


from typing import Tuple, Iterable
import math


def var(r,c,v,N):
    return r*N*N + c*N + v

def read_puzzle(input_path: str):
    """
    Read puzzel from input_path 
    """
    with open(input_path, 'r') as f:
        lines = f.readlines()

    # remove empty lines and strip whitespace
    lines = [line.strip() for line in lines if line.strip()]
    
    grid = []
    for line in lines:
        row = [int(x) for x in line.split()]
        grid.append(row)

    return grid, len(grid)


def exactly_one(literals):
    """
    Given all encoded literals of a cell
    Return a list of clauses relating to the literals"""


    clauses = []

    # At least one number per cell
    clauses.append(literals)

    # At most one number per cell
    for i in range(len(literals)):
        for j in range(i+1, len(literals)):
            clauses.append([-literals[i], -literals[j]])
    
    return clauses

def to_cnf(input_path: str) -> Tuple[Iterable[Iterable[int]], int]:
    """
    Read puzzle from input_path and return (clauses, num_vars).

    - clauses: iterable of iterables of ints (each clause), no trailing 0s
    - num_vars: must be N^3 with N = grid size
    """

    grid, N = read_puzzle(input_path) 
    B = int(math.sqrt(N))

    clauses = []

    # (1) Exactly one value per cell
    for r in range(N):
        for c in range(N):
            literals = [var(r,c,v,N) for v in range(1, N+1)]
            clauses += exactly_one(literals)
    
    # (2) Row constraint: 
    # For each value v and each row r: exactly one column c has v
    for r in range(N):
        for v in range(1, N+1):
            literals = [var(r,c,v,N) for c in range(N)]
            clauses += exactly_one(literals)
    
    # (3) Column constraint:
    # For each value v and each column c: exactly one row r has v
    for c in range(N):
        for v in range(1, N+1):
            literals = [var(r,c,v,N) for r in range(N)]
            clauses += exactly_one(literals)

    # (4) Box constraint:
    for box_r in range(B):
        for box_c in range(B):
            for v in range(1, N+1):
                literals = []
                for r in range(box_r*B, (box_r+1)*B):
                    for c in range(box_c*B, (box_c+1)*B):
                        literals.append(var(r,c,v,N))
                clauses += exactly_one(literals)
    
    # (5) Non-consecutive rule
    for r in range(N):
        for c in range(N):
            for v in range(1, N + 1):
                current = var(r,c,v,N)
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N:
                        if v > 1:
                            clauses.append([-current, -var(nr,nc,v-1,N)])
                        if v < N:
                            clauses.append([-current, -var(nr,nc,v+1,N)])

    # (6) Unit clauses
    for r in range(N):
        for c in range(N):
            v = grid[r][c]
            if v > 0:
                clauses.append([var(r,c,v,N)])
    
    ## Write output file
    num_vars = N*N*N
    num_clauses = len(clauses)

    return clauses, num_vars

  
    


    
