/*
KANDILAS GEORGIOS AM:1115510
KARPETAS APOSTOLOS AM:1115507
*/

/*Q2, syntaktiki + semantiki analysi */
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ===== SEMANTICS  ===== */

typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_VARCHAR,
    TYPE_UNKNOWN
} ColType;

#define MAX_COLS    64
#define MAX_TABLES  128
#define MAX_ALIASES 64

typedef struct {
    char name[64];
    ColType type;
    int varchar_size;   /* mono gia VARCHAR */
} Column;

typedef struct {
    char name[64];
    Column cols[MAX_COLS];
    int col_count;
} Table;

/* to global symbol table - gemizei me kathe CREATE TABLE */
static Table symbol_table[MAX_TABLES];
static int   table_count = 0;

static Table *find_table(const char *name) {
    for (int i = 0; i < table_count; i++) {
        if (strcmp(symbol_table[i].name, name) == 0)
            return &symbol_table[i];
    }
    return NULL;
}

static Column *find_column(Table *t, const char *col) {
    for (int i = 0; i < t->col_count; i++) {
        if (strcmp(t->cols[i].name, col) == 0)
            return &t->cols[i];
    }
    return NULL;
}

static const char *coltype_str(ColType t) {
    switch (t) {
        case TYPE_INT:     return "INT";
        case TYPE_FLOAT:   return "FLOAT";
        case TYPE_VARCHAR: return "VARCHAR";
        default:           return "UNKNOWN";
    }
}

static void sem_create_table(const char *name, Column *cols, int col_count) {
   /* elegxos an uparxei hdh to table */
    if (find_table(name)) {
        fprintf(stderr, "Semantic error: table '%s' already defined.\n", name);
        return;
    }
    /* elegxos gia duplicate cols mesa sto idio table */
    for (int i = 0; i < col_count; i++) {
        for (int j = i + 1; j < col_count; j++) {
            if (strcmp(cols[i].name, cols[j].name) == 0) {
                fprintf(stderr,
                    "Semantic error: duplicate column '%s' in table '%s'.\n",
                    cols[i].name, name);
                return;
            }
        }
    }
    if (table_count >= MAX_TABLES) {
        fprintf(stderr, "Semantic error: too many tables (max %d).\n", MAX_TABLES);
        return;
    }
    Table *t = &symbol_table[table_count++];
    strncpy(t->name, name, sizeof(t->name) - 1);
    t->col_count = col_count;
    for (int i = 0; i < col_count; i++)
        t->cols[i] = cols[i];
}

static void sem_from_check(const char *name) {
    if (!find_table(name))
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", name);
}

static void sem_column_exists(const char *table, const char *col) {
    Table *t = find_table(table);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", table);
        return;
    }
    if (!find_column(t, col))
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, table);
}

static void sem_type_check(const char *table, const char *col, ColType lit_type) {
    Table *t = find_table(table);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", table);
        return;
    }
    Column *c = find_column(t, col);
    if (!c) {
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, table);
        return;
    }
    /* ta INT dexontai INT, ta FLOAT dexontai FLOAT kai INT, ta VARCHAR dexontai VARCHAR */
    int ok = 0;
    if (c->type == TYPE_INT && lit_type == TYPE_INT)
        ok = 1;
    else if (c->type == TYPE_FLOAT && (lit_type == TYPE_INT || lit_type == TYPE_FLOAT))
        ok = 1;
    else if (c->type == TYPE_VARCHAR && lit_type == TYPE_VARCHAR)
        ok = 1;
    if (!ok)
        fprintf(stderr,
            "Semantic error: type mismatch — column '%s.%s' is %s, "
            "but literal is %s.\n",
            table, col, coltype_str(c->type), coltype_str(lit_type));
}

static void sem_type_check_in(const char *table, const char *col,
                               ColType *lit_types, int lit_count) {
    Table *t = find_table(table);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", table);
        return;
    }
    Column *c = find_column(t, col);
    if (!c) {
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, table);
        return;
    }
    /* idia logiki me type_check, apla gia kathe stoixeio tis listas */
    for (int i = 0; i < lit_count; i++) {
        int ok = 0;
        if (c->type == TYPE_INT && lit_types[i] == TYPE_INT)
            ok = 1;
        else if (c->type == TYPE_FLOAT &&
                 (lit_types[i] == TYPE_INT || lit_types[i] == TYPE_FLOAT))
            ok = 1;
        else if (c->type == TYPE_VARCHAR && lit_types[i] == TYPE_VARCHAR)
            ok = 1;
        if (!ok)
            fprintf(stderr,
                "Semantic error: type mismatch in IN list — column '%s.%s' "
                "is %s, but literal is %s.\n",
                table, col, coltype_str(c->type), coltype_str(lit_types[i]));
    }
}

/* ===== END SEMANTICS ===== */

#define MAX_LINES 4096
#define MAX_LINE_LEN 1024

static char *lines[MAX_LINES];
static int   line_count = 0;

int  yylex(void);
void yyerror(const char *s);
extern int yylineno;
extern FILE *yyin;

/* Buffer */
/* buffer gia ta cols tou CREATE TABLE, gemizei me kathe col_def */
#define MAX_COLS_PARSE 64
static Column create_cols[MAX_COLS_PARSE];
static int    create_col_count = 0;

/* to table pou einai active sto trexon SELECT */
static char *current_query_table = NULL;

/* ta cols tou SELECT ta apothikevw edw kai ta elegxo meta to FROM
   giati o parser ta vlepei prin diabasei to table */
#define MAX_SELECT_COLS 64
static char *select_cols[MAX_SELECT_COLS];
static int   select_col_count = 0;

/* buffer typwn gia IN / NOT IN list */
#define MAX_IN_LITERALS 256
static ColType in_literal_types[MAX_IN_LITERALS];
static int     in_literal_count = 0;
%}

%union {
    char  *str;
    int    ival;
    float  fval;
    int    type_tag;
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

%type <str>      col_ref
%type <ival>     comp_op
%type <type_tag> literal type_spec

%%

program
    : stmt_list
    ;

/* eite adeio eite exei statement */
stmt_list
    : /* empty */
    | stmt_list stmt
    ;

/* 2 OPS, CREATE kai SELECT */
stmt
    : create_stmt
    | select_stmt
    ;

create_stmt
    : TOK_CREATE TOK_TABLE TOK_IDENT '(' col_def_list ')' ';'
        {
            sem_create_table($3, create_cols, create_col_count);
            create_col_count = 0;
            free($3);
        }
    ;

col_def_list
    : col_def
    | col_def_list ',' col_def
    ;

col_def
    : TOK_IDENT type_spec
        {
            if (create_col_count < MAX_COLS_PARSE) {
                Column *c = &create_cols[create_col_count++];
                strncpy(c->name, $1, sizeof(c->name) - 1);
                c->type = (ColType)$2;
                c->varchar_size = 0;
            }
            free($1);
        }
    | TOK_IDENT TOK_VARCHAR '(' TOK_INT_LIT ')'
        {
            if ($4 <= 0) {
                fprintf(stderr,
                    "Semantic error: varchar size must be a positive integer.\n");
            }
            if (create_col_count < MAX_COLS_PARSE) {
                Column *c = &create_cols[create_col_count++];
                strncpy(c->name, $1, sizeof(c->name) - 1);
                c->type = TYPE_VARCHAR;
                c->varchar_size = $4;
            }
            free($1);
        }
    ;

type_spec
    : TOK_INT_TYPE   { $$ = TYPE_INT; }
    | TOK_FLOAT_TYPE { $$ = TYPE_FLOAT; }
    ;

select_stmt
    : TOK_SELECT
        {
            if (current_query_table) free(current_query_table);
            current_query_table = NULL;
            select_col_count = 0;
        }
      col_expr_list TOK_FROM TOK_IDENT
        {
            sem_from_check($5);
            current_query_table = strdup($5);
            free($5);
        }
      opt_where opt_group opt_order opt_limit ';'
        {
            /* elegxos ton SELECT cols - deferred giati erthane prin to FROM */
            for (int i = 0; i < select_col_count; i++) {
                char *ref = select_cols[i];
                sem_column_exists(current_query_table, ref);
                free(ref);
            }
            select_col_count = 0;
            if (current_query_table) {
                free(current_query_table);
                current_query_table = NULL;
            }
        }
    ;

col_expr_list
    : TOK_STAR
    | select_col_ref_list
    ;

select_col_ref_list
    : col_ref
        {
            if (select_col_count < MAX_SELECT_COLS)
                select_cols[select_col_count++] = $1;
            else
                free($1);
        }
    | select_col_ref_list ',' col_ref
        {
            if (select_col_count < MAX_SELECT_COLS)
                select_cols[select_col_count++] = $3;
            else
                free($3);
        }
    ;

col_ref_list
    : col_ref
        {
            sem_column_exists(current_query_table, $1);
            free($1);
        }
    | col_ref_list ',' col_ref
        {
            sem_column_exists(current_query_table, $3);
            free($3);
        }
    ;

col_ref
    : TOK_IDENT
        {
            $$ = strdup($1);
            free($1);
        }
    ;

opt_where
    : /* empty */
    | TOK_WHERE condition
    ;

condition
    : condition TOK_OR  condition
    | condition TOK_AND condition
    | TOK_NOT condition
    | '(' condition ')'
    | col_ref comp_op literal
        {
            sem_type_check(current_query_table, $1, (ColType)$3);
            free($1);
        }
    | col_ref TOK_IN '('
        { in_literal_count = 0; }
      in_literal_list ')'
        {
            sem_type_check_in(current_query_table, $1, in_literal_types, in_literal_count);
            free($1);
        }
    | col_ref TOK_NOT TOK_IN '('
        { in_literal_count = 0; }
      in_literal_list ')'
        {
            sem_type_check_in(current_query_table, $1, in_literal_types, in_literal_count);
            free($1);
        }
    ;

comp_op
    : TOK_EQ  { $$ = 0; }
    | TOK_NEQ { $$ = 1; }
    | TOK_GT  { $$ = 2; }
    | TOK_LT  { $$ = 3; }
    | TOK_GTE { $$ = 4; }
    | TOK_LTE { $$ = 5; }
    ;

literal
    : TOK_INT_LIT   { $$ = TYPE_INT; }
    | TOK_FLOAT_LIT { $$ = TYPE_FLOAT; }
    | TOK_STR_LIT   { $$ = TYPE_VARCHAR; free($1); }
    ;

in_literal_list
    : literal
        {
            if (in_literal_count < MAX_IN_LITERALS)
                in_literal_types[in_literal_count++] = (ColType)$1;
        }
    | in_literal_list ',' literal
        {
            if (in_literal_count < MAX_IN_LITERALS)
                in_literal_types[in_literal_count++] = (ColType)$3;
        }
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

void yyerror(const char *s) {
    for (int i = 0; i < line_count && i < yylineno; i++) {
        printf("%s\n", lines[i]);
    }
    printf("Syntax error on line %d: %s\n", yylineno, s);
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
        printf("Syntactic analysis successful.\n");
    }

    for (int i = 0; i < line_count; i++)
        free(lines[i]);

    return result;
}
