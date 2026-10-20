# Data Structures

This repository contains coursework and programming exercises for a Data
Structures course. The implementations are primarily written in C, with one
Python utility for generating expressions used by the first exercise set.

## Contents

### `set1`

Fundamental data-structure exercises:

- `askisi1.c` - stack-based validation of bracketed arithmetic expressions.
- `askisi2.c` - binary search tree insertion, search, traversal, and deletion.
- `askisi3.c` - binary-tree traversals, including level-order traversal using a
  queue.
- `askisi4.c` - binary-tree height and node-depth calculations.
- `askisi5.c` - reconstruction of a binary tree from inorder and preorder
  traversals.
- `generator.py` - generates valid and invalid arithmetic expressions for
  testing `askisi1`.
- `PROJECT1_1108254_1115507.docx` - project documentation.

The `askisi1` file without an extension is a precompiled executable.

### `set2`

Exercises based on the supplied COVID-19 trade dataset:

- `part1/ex1.c` - merge sort and counting sort.
- `part1/ex2.c` - quicksort and heapsort.
- `part1/ex3.c` - date sorting with binary and interpolation search.
- `part1/ex4.c` - additional date-search implementations.
- `part2/exa.c` - AVL tree operations.
- `part2/exb.c` - binary-search-tree operations and minimum/maximum queries.
- `part2/exc.c` - hash-table operations.
- `part2/final.c` - combined binary-search-tree and hash-table solution.
- `PROJECT-DS-2026-final.docx` - project documentation.

Each `part1` and `part2` directory includes the CSV file expected by its
programs. `part1/ex2.c` looks for `test_data.csv`; if it is not available,
create or rename a compatible copy of the included dataset before running it.
The `ex4` and `final` files without extensions are precompiled executables.

### `final`

The final submitted versions are organized into:

- `PART I` - sorting, searching, and a threaded search comparison in
  `part1_ex1.c` through `part1_ex4.c`.
- `PART II` - AVL tree, binary-search-tree, hash-table, and combined
  implementations in `part2_exA.c`, `part2_exB.c`, `part2_exC.c`, and
  `part2_final.c`.
- `PROJECT2_1115507_1108254.pdf` - final project documentation.

`PART I` and `PART II` each include the CSV dataset expected by their C
programs.

## Requirements

- GCC or another C compiler
- Python 3 (only for `set1/generator.py`)
- POSIX threads support for `final/PART I/part1_ex4.c`

## Building and running

Compile a program from the directory containing its source and, when
applicable, its CSV input. For example:

```sh
cd set1
gcc -std=c11 -Wall -Wextra -O2 askisi1.c -o askisi1
./askisi1
python3 generator.py
```

The menu-driven programs can be built and run in the same way:

```sh
cd set2/part1
gcc -std=c11 -Wall -Wextra -O2 ex1.c -o ex1
./ex1
```

For programs that read the CSV file, run the executable from the directory
containing that CSV so the source's relative filename resolves correctly.
Examples:

```sh
cd set2/part2
gcc -std=c11 -Wall -Wextra -O2 final.c -o final
./final

cd "../../final/PART I"
gcc -std=c11 -Wall -Wextra -O2 part1_ex4.c -o part1_ex4 -pthread
./part1_ex4
```

The programs are interactive and display their available operations after
starting. Compiled executables are platform-dependent; rebuilding from the
source is recommended on another operating system or architecture.

## Dataset

The CSV files are copies of the same trade dataset. Its columns include
direction, year, date, weekday, country, commodity, transport mode, measure,
value, and cumulative value.
