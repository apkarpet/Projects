/*
KANDILAS GEORGIOS AM:1115510
KARPETAS APOSTOLOS AM:1115507
*/

/* Q2, idio me Q1 ala tora exoume kai semantics.h */
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.tab.h"
%}

/* ENTOLES FLEX */
%option yylineno
%option noyywrap
%option noinput
%option nounput
%option case-insensitive

%%

"/*"([^*]|\*+[^*/])*\*+"/"   { /* skip */ }
"--"[^\n]*                    { /* skip */ }

"select"    { return TOK_SELECT; }
"from"      { return TOK_FROM; }
"where"     { return TOK_WHERE; }
"limit"     { return TOK_LIMIT; }
"group"     { return TOK_GROUP; }
"order"     { return TOK_ORDER; }
"by"        { return TOK_BY; }
"in"        { return TOK_IN; }
"and"       { return TOK_AND; }
"or"        { return TOK_OR; }
"not"       { return TOK_NOT; }
"create"    { return TOK_CREATE; }
"table"     { return TOK_TABLE; }
"int"       { return TOK_INT_TYPE; }
"float"     { return TOK_FLOAT_TYPE; }
"varchar"   { return TOK_VARCHAR; }
"!="    { return TOK_NEQ; }
">="    { return TOK_GTE; }
"<="    { return TOK_LTE; }
">"     { return TOK_GT; }
"<"     { return TOK_LT; }
"="     { return TOK_EQ; }
"*"     { return TOK_STAR; }
[.,;()] { return yytext[0]; }

"-"?[0-9]+"."[0-9]+  {
    yylval.fval = atof(yytext);
    return TOK_FLOAT_LIT;
}

"-"?[0-9]+  {
    yylval.ival = atoi(yytext);
    return TOK_INT_LIT;
}

'[^']*'  {
    int len = strlen(yytext) - 2;
    yylval.str = (char *)malloc(len + 1);
    strncpy(yylval.str, yytext + 1, len);
    yylval.str[len] = '\0';
    return TOK_STR_LIT;
}

[a-zA-Z_][a-zA-Z0-9_]*  {
    yylval.str = strdup(yytext);
    return TOK_IDENT;
}

[ \t\r\n]+  { /* skip */ }

.  {
    fprintf(stderr, "Lexer error: unexpected character '%s' on line %d\n",
            yytext, yylineno);
}

%%
