/*
KANDILAS GEORGIOS AM:1115510
KARPETAS APOSTOLOS AM:1115507
*/

/*Q3, prosthiki JOIN me aliases kai elegxos gia ambiguous cols */
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ===== SEMANTICS ===== */

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

typedef struct {
    char alias[64];
    char table[64];   /* to pragmatiko onoma tis tablas */
} AliasEntry;

/* to global symbol table - gemizei me kathe CREATE TABLE */
static Table symbol_table[MAX_TABLES];
static int   table_count = 0;

/* alias map kai active tables - reset se kathe neo SELECT */
static AliasEntry  alias_map[MAX_ALIASES];
static int         alias_count = 0;

static const char *active_tables[MAX_ALIASES];
static int         active_table_count = 0;

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

static const char *sem_resolve_alias(const char *name) {
    for (int i = 0; i < alias_count; i++) {
        if (strcmp(alias_map[i].alias, name) == 0)
            return alias_map[i].table;
    }
    return name; /* den einai alias, epistrefoume ws exei */
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
    const char *real = sem_resolve_alias(name);
    if (!find_table(real))
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", real);
}

static void sem_column_exists(const char *table, const char *col) {
    const char *real = sem_resolve_alias(table);
    Table *t = find_table(real);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", real);
        return;
    }
    if (!find_column(t, col))
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, real);
}

static void sem_type_check(const char *table, const char *col, ColType lit_type) {
    const char *real = sem_resolve_alias(table);
    Table *t = find_table(real);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", real);
        return;
    }
    Column *c = find_column(t, col);
    if (!c) {
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, real);
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
            real, col, coltype_str(c->type), coltype_str(lit_type));
}

static void sem_type_check_in(const char *table, const char *col,
                               ColType *lit_types, int lit_count) {
    const char *real = sem_resolve_alias(table);
    Table *t = find_table(real);
    if (!t) {
        fprintf(stderr, "Semantic error: unknown table '%s'.\n", real);
        return;
    }
    Column *c = find_column(t, col);
    if (!c) {
        fprintf(stderr,
            "Semantic error: column '%s' not found in table '%s'.\n",
            col, real);
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
                real, col, coltype_str(c->type), coltype_str(lit_types[i]));
    }
}

static void sem_register_alias(const char *alias, const char *table) {
    /* den epitrepoume to idio alias dis sto idio query */
    for (int i = 0; i < alias_count; i++) {
        if (strcmp(alias_map[i].alias, alias) == 0) {
            fprintf(stderr,
                "Semantic error: alias '%s' already defined in this query.\n",
                alias);
            return;
        }
    }
    if (alias_count >= MAX_ALIASES) {
        fprintf(stderr, "Semantic error: too many aliases.\n");
        return;
    }
    AliasEntry *e = &alias_map[alias_count++];
    strncpy(e->alias, alias, sizeof(e->alias) - 1);
    strncpy(e->table, table, sizeof(e->table) - 1);
}

static void sem_set_query_tables(const char **names, int count) {
    active_table_count = 0;
    for (int i = 0; i < count && i < MAX_ALIASES; i++)
        active_tables[active_table_count++] = names[i];
}

static void sem_column_in_query(const char *table_or_null, const char *col) {
    if (table_or_null) {
        /* qualified ref (tabla.col) - apeftheias elegxos */
        sem_column_exists(table_or_null, col);
        return;
    }
    /* bare col: psaxnoume se oles tis active tables */
    if (active_table_count == 0) return;
    int found = 0;
    for (int i = 0; i < active_table_count; i++) {
        const char *real = sem_resolve_alias(active_tables[i]);
        Table *t = find_table(real);
        if (t && find_column(t, col))
            found++;
    }
    if (found == 0)
        fprintf(stderr,
            "Semantic error: column '%s' not found in any active table.\n", col);
    else if (found > 1)
        /* ambiguous - uparxei se perissoteres tables, prepei na to kaneis qualify */
        fprintf(stderr,
            "Semantic warning: column '%s' is ambiguous (found in %d tables).\n",
            col, found);
}

static void sem_reset_aliases(void) {
    alias_count        = 0;
    active_table_count = 0;
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

/* lista twn tablon (h aliases) pou einai active sto trexon SELECT+JOINs */
#define MAX_QUERY_TABLES 64
static const char *query_tables[MAX_QUERY_TABLES];
static int         query_table_count = 0;

static void add_query_table(const char *name) {
    if (query_table_count < MAX_QUERY_TABLES)
        query_tables[query_table_count++] = name;
}

/* ta SELECT cols ta apothikevw kai ta elegxo meta ta FROM/JOIN
   giati o parser ta vlepei PRIN mathi pies tables einai active */
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
%token TOK_CREATE TOK_TABLE TOK_JOIN TOK_ON TOK_AS
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

%type <str>      col_ref qualified_col_ref
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
        { sem_reset_aliases(); query_table_count = 0; select_col_count = 0; }
      col_expr_list TOK_FROM table_ref join_list
        {
            /* tora pou kseroume oles tis tables/aliases, orizoume to query context */
            sem_set_query_tables(query_tables, query_table_count);
        }
      opt_where opt_group opt_order opt_limit ';'
        {
            /* elegxos ton SELECT cols - deferred giati erthane prin ta FROM/JOIN */
            for (int i = 0; i < select_col_count; i++) {
                char *ref = select_cols[i];
                char *dot = strchr(ref, '.');
                if (dot) {
                    *dot = '\0';
                    sem_column_in_query(ref, dot + 1);
                } else {
                    sem_column_in_query(NULL, ref);
                }
                free(ref);
            }
            select_col_count = 0;
        }
    ;

table_ref
    : TOK_IDENT
        {
            sem_from_check($1);
            add_query_table(strdup($1));
            free($1);
        }
    | TOK_IDENT TOK_AS TOK_IDENT
        {
            sem_from_check($1);
            sem_register_alias($3, $1);
            add_query_table(strdup($3));
            free($1); free($3);
        }
    ;

join_list
    : /* empty */
    | join_list TOK_JOIN table_ref TOK_ON qualified_col_ref TOK_EQ qualified_col_ref
        {
            /* elegxos kai twn duo merWN tou ON col1 = col2 */
            char *dot;
            dot = strchr($5, '.'); *dot = '\0'; sem_column_exists($5, dot + 1);
            dot = strchr($7, '.'); *dot = '\0'; sem_column_exists($7, dot + 1);
            free($5); free($7);
        }
    ;

qualified_col_ref
    : TOK_IDENT '.' TOK_IDENT
        {
            int len = strlen($1) + 1 + strlen($3) + 1;
            $$ = malloc(len);
            snprintf($$, len, "%s.%s", $1, $3);
            free($1); free($3);
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
            char *dot = strchr($1, '.');
            if (dot) {
                *dot = '\0';
                sem_column_in_query($1, dot + 1);
            } else {
                sem_column_in_query(NULL, $1);
            }
            free($1);
        }
    | col_ref_list ',' col_ref
        {
            char *dot = strchr($3, '.');
            if (dot) {
                *dot = '\0';
                sem_column_in_query($3, dot + 1);
            } else {
                sem_column_in_query(NULL, $3);
            }
            free($3);
        }
    ;

/* col_ref epistrefei "tabla.col" h aplo "col" san string */
col_ref
    : TOK_IDENT
        {
            $$ = strdup($1);
            free($1);
        }
    | TOK_IDENT '.' TOK_IDENT
        {
            int len = strlen($1) + 1 + strlen($3) + 1;
            $$ = malloc(len);
            snprintf($$, len, "%s.%s", $1, $3);
            free($1); free($3);
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
            /* an exei teleia einai qualified (tabla.col), alliws psaxnoume oles */
            char *dot = strchr($1, '.');
            if (dot) {
                *dot = '\0';
                sem_type_check($1, dot + 1, (ColType)$3);
            } else {
                for (int i = 0; i < query_table_count; i++) {
                    const char *real = sem_resolve_alias(query_tables[i]);
                    sem_type_check(real, $1, (ColType)$3);
                    break; /* mono sto proto match, alliws vgainoun diples errors */
                }
            }
            free($1);
        }
    | col_ref TOK_IN '('
        { in_literal_count = 0; }
      in_literal_list ')'
        {
            char *dot = strchr($1, '.');
            if (dot) {
                *dot = '\0';
                sem_type_check_in($1, dot + 1, in_literal_types, in_literal_count);
            } else {
                for (int i = 0; i < query_table_count; i++) {
                    const char *real = sem_resolve_alias(query_tables[i]);
                    sem_type_check_in(real, $1, in_literal_types, in_literal_count);
                    break;
                }
            }
            free($1);
        }
    | col_ref TOK_NOT TOK_IN '('
        { in_literal_count = 0; }
      in_literal_list ')'
        {
            char *dot = strchr($1, '.');
            if (dot) {
                *dot = '\0';
                sem_type_check_in($1, dot + 1, in_literal_types, in_literal_count);
            } else {
                for (int i = 0; i < query_table_count; i++) {
                    const char *real = sem_resolve_alias(query_tables[i]);
                    sem_type_check_in(real, $1, in_literal_types, in_literal_count);
                    break;
                }
            }
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
