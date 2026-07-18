# check_indentation.py
# jasper sinclair

import os
import re


def check_file(path):
    has_tabs = False
    has_spaces = False
    mixed_lines = []

    with open(path, "r", encoding="utf-8", errors="ignore") as source:
        for line_number, line in enumerate(source, 1):
            if line.startswith("\t"):
                has_tabs = True
            if re.match(r"^ {1,8}\S", line):
                has_spaces = True
            if re.match(r"^\t+ +", line) or re.match(r"^ +\t+", line):
                mixed_lines.append(line_number)

    return has_tabs, has_spaces, mixed_lines


def scan_directory(root):
    print("Scanning:", root)
    print()

    issue_count = 0
    skipped = {".git", ".venv", "venv", "nnue_env", "__pycache__"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in skipped]

        for name in filenames:
            if not name.endswith(".py"):
                continue

            path = os.path.join(dirpath, name)
            has_tabs, has_spaces, mixed = check_file(path)

            if mixed or (has_tabs and has_spaces):
                issue_count += 1
                print(f"WARNING: {path}")

                if has_tabs and has_spaces:
                    print("  File contains both tab- and space-indented lines")

                if mixed:
                    print("  Mixed indentation lines:", mixed)

                print()

    if issue_count == 0:
        print("No indentation problems found.")

    return issue_count


if __name__ == "__main__":
    raise SystemExit(1 if scan_directory(".") else 0)
