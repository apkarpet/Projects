# LSH: a tiny Unix shell in C

A minimal command-line shell, about 200 lines of C, written by following Stephen Brennan's
tutorial [*Tutorial – Write a Shell in C*](https://brennan.io/2015/01/16/write-a-shell-in-c/).
It shows the core loop every shell runs: **read** a line, **parse** it into arguments,
**execute** it.

## Demo

```text
$ gcc -std=c17 -Wall -Wextra shell.c -o lsh
$ ./lsh
> help
Apostolos Karpetas's LSH
Type program names and arguments, and hit enter.
The following are built in:
    cd
    help
    exit
Use the man command for info on other programs.
> echo hello from lsh
hello from lsh
> cd /tmp
> pwd
/tmp
> ls /nonexistent
ls: cannot access '/nonexistent': No such file or directory
> exit
```

## How it works

| Step | Function | What happens |
| --- | --- | --- |
| Read | `lsh_read_line` | reads a line from standard input with `getline` |
| Parse | `lsh_split_line` | splits it on whitespace with `strtok`, growing the token array with `realloc` as needed |
| Execute | `lsh_execute` | runs a built-in if the command is one, otherwise launches a program |
| Launch | `lsh_launch` | `fork()`s; the child replaces itself with the program through `execvp()`, the parent `waitpid()`s until it finishes |

Built-ins (`cd`, `help`, `exit`) have to run inside the shell process itself: `cd` in a child
process would change the child's directory, not the shell's. They're looked up in a table of
names and function pointers, so adding one is a single entry.

## Limits

Like the tutorial, it has no quoting, pipes (`|`), redirection (`>`), globbing or background
jobs (`&`). Arguments are split on whitespace only.

## Build

Needs a C compiler on Linux or macOS (it uses POSIX `fork`, `execvp` and `waitpid`):

```sh
gcc -std=c17 -Wall -Wextra shell.c -o lsh
./lsh
```
