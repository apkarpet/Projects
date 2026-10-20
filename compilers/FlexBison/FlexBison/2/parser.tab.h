/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

#ifndef YY_YY_PARSER_TAB_H_INCLUDED
# define YY_YY_PARSER_TAB_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    TOK_SELECT = 258,              /* TOK_SELECT  */
    TOK_FROM = 259,                /* TOK_FROM  */
    TOK_WHERE = 260,               /* TOK_WHERE  */
    TOK_LIMIT = 261,               /* TOK_LIMIT  */
    TOK_GROUP = 262,               /* TOK_GROUP  */
    TOK_ORDER = 263,               /* TOK_ORDER  */
    TOK_BY = 264,                  /* TOK_BY  */
    TOK_IN = 265,                  /* TOK_IN  */
    TOK_AND = 266,                 /* TOK_AND  */
    TOK_OR = 267,                  /* TOK_OR  */
    TOK_NOT = 268,                 /* TOK_NOT  */
    TOK_CREATE = 269,              /* TOK_CREATE  */
    TOK_TABLE = 270,               /* TOK_TABLE  */
    TOK_INT_TYPE = 271,            /* TOK_INT_TYPE  */
    TOK_FLOAT_TYPE = 272,          /* TOK_FLOAT_TYPE  */
    TOK_VARCHAR = 273,             /* TOK_VARCHAR  */
    TOK_EQ = 274,                  /* TOK_EQ  */
    TOK_NEQ = 275,                 /* TOK_NEQ  */
    TOK_GT = 276,                  /* TOK_GT  */
    TOK_LT = 277,                  /* TOK_LT  */
    TOK_GTE = 278,                 /* TOK_GTE  */
    TOK_LTE = 279,                 /* TOK_LTE  */
    TOK_STAR = 280,                /* TOK_STAR  */
    TOK_IDENT = 281,               /* TOK_IDENT  */
    TOK_STR_LIT = 282,             /* TOK_STR_LIT  */
    TOK_INT_LIT = 283,             /* TOK_INT_LIT  */
    TOK_FLOAT_LIT = 284            /* TOK_FLOAT_LIT  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 205 "parser.y"

    char  *str;
    int    ival;
    float  fval;
    int    type_tag;

#line 100 "parser.tab.h"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_PARSER_TAB_H_INCLUDED  */
