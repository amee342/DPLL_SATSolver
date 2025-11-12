#!/usr/bin/env python3
import os
import time
import pandas as pd
from encoder import to_cnf as encode_puzzle
from solver import solve_cnf

# Directory containing all puzzle files (e.g., txt Sudoku puzzles)
PUZZLE_DIR = "puzzles"
OUTPUT_FILE = "solver_results.xlsx"

def test_all_puzzles(folder_path):
    results = []
    puzzle_files = [f for f in os.listdir(folder_path) if f.endswith(".txt") and f.startswith("puzzle1")]

    print(f"Found {len(puzzle_files)} puzzle files in '{folder_path}'")

    for filename in puzzle_files:
        filepath = os.path.join(folder_path, filename)
        print(f"Solving: {filename} ...")

        try:
            # Encode puzzle into CNF clauses and number of variables
            clauses, num_vars = encode_puzzle(filepath)

            # Measure solving time
            start = time.time()
            result, model = solve_cnf(clauses, num_vars)
            end = time.time()

            elapsed = round(end - start, 4)
            results.append({
                "puzzle_name": filename,
                "result": result,
                "time_seconds": elapsed,
                "num_clauses": len(clauses),
                "num_variables": num_vars
            })

            print(f" → {result} ({elapsed:.4f}s)")

        except Exception as e:
            results.append({
                "puzzle_name": filename,
                "result": f"Error: {str(e)}",
                "time_seconds": None,
                "num_clauses": None,
                "num_variables": None
            })
            print(f" ✗ Failed on {filename}: {e}")

    return results


def save_results_to_excel(results, output_path):
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False)
    print(f"\n✅ Results saved to {output_path}")


if __name__ == "__main__":
    if not os.path.exists(PUZZLE_DIR):
        print(f"Error: folder '{PUZZLE_DIR}' not found.")
    else:
        results = test_all_puzzles(PUZZLE_DIR)
        save_results_to_excel(results, OUTPUT_FILE)