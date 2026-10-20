#define _POSIX_C_SOURCE 200809L

#define LSH_RL_BUFSIZE 1024
#define LSH_TOK_BUFSIZE 64
#define LSH_TOK_DELIM " \t\r\n\a"

#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int lsh_execute(char **args);

char **lsh_split_line(char *line)
{
    int bufsize = LSH_TOK_BUFSIZE, position = 0;
    char **tokens = malloc((size_t)bufsize * sizeof(*tokens));
    char *token;

    if (!tokens) {
        fprintf(stderr, "lsh: allocation error\n");
        exit(EXIT_FAILURE);
    }

    token = strtok(line, LSH_TOK_DELIM);
    while (token != NULL) {
        tokens[position] = token;
        position++;

        if (position >= bufsize) {
            bufsize += LSH_TOK_BUFSIZE;
            char **resized_tokens = realloc(tokens,
                                           (size_t)bufsize * sizeof(*tokens));
            if (!resized_tokens) {
                free(tokens);
                fprintf(stderr, "lsh: allocation error\n");
                exit(EXIT_FAILURE);
            }
            tokens = resized_tokens;
        }
        token = strtok(NULL, LSH_TOK_DELIM);
    }

    tokens[position] = NULL;
    return tokens;
}

int lsh_launch(char **args)
{
    pid_t pid, wpid;
    int status;

    pid = fork();
    if (pid == 0) {
        execvp(args[0], args);
        perror("lsh");
        exit(EXIT_FAILURE);
    } else if (pid < 0) {
        perror("lsh");
        return 1;
    } else {
        do {
            wpid = waitpid(pid, &status, WUNTRACED);
        } while ((wpid == -1 && errno == EINTR) ||
                 (wpid > 0 && !WIFEXITED(status) && !WIFSIGNALED(status)));

        if (wpid == -1) {
            perror("lsh");
        }
    }

    return 1;
}

char *lsh_read_line(void)
{
    char *line = NULL;
    size_t bufsize = 0;

    if (getline(&line, &bufsize, stdin) == -1){
        if(feof(stdin)) {
            exit(EXIT_SUCCESS);
        } else {
            perror("readline");
            exit(EXIT_FAILURE);
        }
    }

    return line;
}

void lsh_loop(void)
{
    char *line;
    char **args;
    int status;

    do {
        printf("> ");
        fflush(stdout);
        line = lsh_read_line();
        args = lsh_split_line(line);
        status = lsh_execute(args);

        free(line);
        free(args);
    } while (status);
}

int lsh_cd(char **args);
int lsh_help(char **args);
int lsh_exit(char **args);

char *builtin_str[] = {
    "cd",
    "help",
    "exit"
};

int (*builtin_func[]) (char**) = {
    &lsh_cd,
    &lsh_help,
    &lsh_exit
};

int lsh_num_builtins() {
    return sizeof(builtin_str) / sizeof(char *);
}

int lsh_execute(char **args)
{
    int i;

    if (args[0] == NULL) {
        return 1;
    }

    for (i=0; i<lsh_num_builtins(); i++) {
        if (strcmp(args[0], builtin_str[i]) == 0) {
            return (*builtin_func[i])(args);
        }
    }
    return lsh_launch(args);
}

int main(void)
{
    lsh_loop();

    return EXIT_SUCCESS;
}

int lsh_cd(char **args) 
{
    if (args[1] == NULL) {
        fprintf(stderr, "lsh: expected argument to \"cd\"\n");
    } else {
        if (chdir(args[1]) != 0) {
            perror("lsh");
        }
    }
    return 1;
}

int lsh_help (char **args)
{
    int i;
    (void)args;
    printf("Apostolos Karpetas's LSH\n");
    printf("Type program names and arguments, and hit enter.\n");
    printf("The following are built in:\n");

    for (i=0; i<lsh_num_builtins(); i++) {
        printf("    %s\n", builtin_str[i]);
    }
    printf("Use the man command for info on other programs.\n");
    return 1;
}

int lsh_exit(char **args)
{
    (void)args;
    return 0;
}
