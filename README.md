# Projects

An index of my projects, from first-year C exercises to the tools I use every week. Each
project lives in its own repository with a full README, a demo and build instructions.

## Personal projects

| Project | What it is | Built with |
| --- | --- | --- |
| [**EuroLeague Fantasy assistant**](https://github.com/apkarpet/euroleague-fantasy) | Self-hosted helper for the EuroLeague Fantasy Challenge: player projections, an exact team optimiser (mixed-integer programming), a Monte Carlo round simulator and live round tracking. Backtested on past rounds: its teams scored 22% more than the same optimiser fed season averages. | Python, numpy, scipy, vanilla JS |
| [**CEID Notes**](https://github.com/apkarpet/ceid-notes) | Open study guides and an exam archive for the Computer Engineering & Informatics courses at the University of Patras, live at [ceid.gr](https://ceid.gr/). In Greek. | static site, PDF |
| [**LSH**](selfmade/c_c++) (in this repo) | A tiny Unix shell in C: read, parse, `fork` + `execvp`, with `cd`, `help` and `exit` built in. Written following Stephen Brennan's tutorial. | C, POSIX |

![EuroLeague Fantasy assistant](https://raw.githubusercontent.com/apkarpet/euroleague-fantasy/main/docs/screenshots/team.png)

## University coursework

| Repository | Course | Highlights |
| --- | --- | --- |
| [**Compilers**](https://github.com/apkarpet/Compilers) | Compilers (2nd year) | A SQL compiler in Flex and Bison with semantic checks (unknown tables and columns, type mismatches, joins and aliases), and a Tkinter course-recommendation app that collects data from public APIs. Both graded 10/10. |
| [**DataStructures**](https://github.com/apkarpet/DataStructures) | Data Structures (2nd year) | Sorting and searching 111,438 real trade records, AVL trees, hash tables, a multithreaded search race. Graded 9.5/10. |
| [**RISC-V**](https://github.com/apkarpet/RISC-V) | Computer Architecture | RISC-V assembly for RARS: endianness, overflow, floating point, trap handlers, cache access patterns. |
| [**Clang**](https://github.com/apkarpet/Clang) | Introduction to Programming (1st year) | 80+ C programs, lab by lab, with a one-command build script. |

## Layout of this repository

```
selfmade/c_c++/   LSH, the tiny shell (README, demo and build steps inside)
```

The other projects used to be copied in here as folders. They now live only in their own
repositories, linked above, so there is one up-to-date copy of each.
