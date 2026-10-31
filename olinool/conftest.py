import pathlib
import sys

for sib in ("python", "../moolam/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent / sib).resolve()))
