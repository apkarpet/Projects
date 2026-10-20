# Projects

This repository is a collection of programming exercises, university
coursework, and personal experiments. The projects cover systems programming,
data structures, compiler construction, Python applications, and RISC-V
assembly.

## Repository layout

| Directory | Description |
| --- | --- |
| [`clang/`](clang/) | C programming exercises, laboratory work, and algorithms |
| [`compilers/`](compilers/) | Flex/Bison SQL compiler coursework and a Python course-recommendation application |
| [`datastructs/`](datastructs/) | C and Python data-structure exercises, sorting/searching implementations, and project submissions |
| [`riscv/`](riscv/) | RISC-V assembly labs and architecture experiments for the RARS simulator |
| [`selfmade/`](selfmade/) | Independent projects, including a small C shell implementation in [`selfmade/c_c++/`](selfmade/c_c++/) |

Each project directory contains its own README with more specific
documentation, prerequisites, build commands, and usage instructions.

## Languages and tools

The repository includes:

- C and C++ programs built with GCC or another compatible compiler
- Python 3 scripts and desktop applications
- Flex and Bison lexer/parser projects
- RISC-V assembly programs intended for RARS
- Coursework reports, sample data, and other supporting documents

Build products such as object files, executables, Python bytecode, and cache
directories are intentionally excluded from the top-level repository. Rebuild
them locally using the instructions in the relevant project README.

## Working with the projects

Start by opening the README in the project you want to use. Most C programs
can be compiled with GCC from their source directory, Python applications
list their dependencies in `requirements.txt`, and the RISC-V labs can be
opened directly in RARS.

