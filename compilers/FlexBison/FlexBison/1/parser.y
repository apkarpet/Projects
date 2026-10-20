/* KANDILAS GEORGIOS AM:1115510
KARPETAS APOSTOLOS AM:1115507
*/

/*Q1, apla syntaktiki analysi */
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINES 4096
#define MAX_LINE_LEN 1024

/* Buffer */
static char *lines[MAX_LINES];
static int   line_count = 0;

int  yylex(void);
void yyerror(const char *s);
extern int yylineno;
extern FILE *yyin;
%}

%union {
    char  *str;
    int    ival;
    float  fval;
}

%token TOK_SELECT TOK_FROM TOK_WHERE TOK_LIMIT TOK_GROUP TOK_ORDER TOK_BY
%token TOK_IN TOK_AND TOK_OR TOK_NOT
%token TOK_CREATE TOK_TABLE
%token TOK_INT_TYPE TOK_FLOAT_TYPE TOK_VARCHAR
%token TOK_EQ TOK_NEQ TOK_GT TOK_LT TOK_GTE TOK_LTE
%token TOK_STAR

%token <str>  TOK_IDENT TOK_STR_LIT
%token <ival> TOK_INT_LIT
%token <fval> TOK_FLOAT_LIT

/* protereotita: OR < AND < NOT */
%left  TOK_OR
%left  TOK_AND
%right TOK_NOT

%type <str> col_ref

%%

program
    : stmt_list
    ;

stmt_list
    : /* empty */ 
    | stmt_list stmt
    ;

stmt
    : create_stmt
    | select_stmt
    ;
 
create_stmt
    : TOK_CREATE TOK_TABLE TOK_IDENT '(' col_def_list ')' ';'
    ;

col_def_list
    : col_def
    | col_def_list ',' col_def
    ;

col_def
    : TOK_IDENT type_spec
    | TOK_IDENT TOK_VARCHAR '(' TOK_INT_LIT ')'
    ;

type_spec
    : TOK_INT_TYPE
    | TOK_FLOAT_TYPE
    ;

select_stmt
    : TOK_SELECT col_expr_list TOK_FROM TOK_IDENT opt_where opt_group opt_order opt_limit ';'
    ;

col_expr_list
    : TOK_STAR
    | col_ref_list
    ;

col_ref_list
    : col_ref
    | col_ref_list ',' col_ref
    ;

col_ref
    : TOK_IDENT { $$ = strdup($1); }
    | TOK_IDENT '.' TOK_IDENT
        {
            int len = strlen($1) + 1 + strlen($3) + 1;
            $$ = malloc(len);
            snprintf($$, len, "%s.%s", $1, $3);
        }
    ;

opt_where
    : /* empty */
    | TOK_WHERE condition
    ;

condition
    : condition TOK_OR condition
    | condition TOK_AND condition
    | TOK_NOT condition
    | '(' condition ')'
    | col_ref comp_op literal
    | col_ref TOK_IN '(' in_literal_list ')'
    | col_ref TOK_NOT TOK_IN '(' in_literal_list ')'
    ;

comp_op
    : TOK_EQ
    | TOK_NEQ
    | TOK_GT
    | TOK_LT
    | TOK_GTE
    | TOK_LTE
    ;

literal
    : TOK_INT_LIT
    | TOK_FLOAT_LIT
    | TOK_STR_LIT
    ;

in_literal_list
    : literal
    | in_literal_list ',' literal
    ;

opt_group
    : /* empty */
    | TOK_GROUP TOK_BY col_ref_list
    ;

opt_order
    : /* empty */
    | TOK_ORDER TOK_BY col_ref_list
    ;

opt_limit
    : /* empty */
    | TOK_LIMIT TOK_INT_LIT
    ;

%%

/* Error sinartisi */
void yyerror(const char *s) {
    for (int i = 0; i < line_count && i < yylineno; i++) {
        printf("%s\n", lines[i]);
    }
    printf("%s - line %d\n", s, yylineno);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input.sql>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        perror(argv[1]);
        return 1;
    }
    
    char buf[MAX_LINE_LEN];
    while (fgets(buf, sizeof(buf), f) && line_count < MAX_LINES) {
        int len = strlen(buf);
        if (len > 0 && buf[len - 1] == '\n') buf[len - 1] = '\0';
        lines[line_count++] = strdup(buf);
    }

    rewind(f); 
    yyin = f;

    int result = yyparse();
    fclose(f);

    if (result == 0) {
        for (int i = 0; i < line_count; i++)
            printf("%s\n", lines[i]);
        printf("Syntactic analysis successful, program is syntactically correct.\n");
    }

    return result;
}