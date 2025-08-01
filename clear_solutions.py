import nbformat
import argparse

parser = argparse.ArgumentParser(description="Clear solutions from notebook cells.")
parser.add_argument("path", help="Path to the input notebook file.")
args = parser.parse_args()
path = args.path

nb = nbformat.read(path, as_version=4)

for cell in nb.cells:
    if "tags" in cell.metadata and "sol" in cell.metadata["tags"]:
        cell.source = ""
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None

nbformat.write(nb, "output_empty_solutions.ipynb")
