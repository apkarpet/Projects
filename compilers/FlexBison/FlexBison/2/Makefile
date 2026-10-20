# mySQLq Compiler Makefile
#
# Works from PowerShell (mingw32-make) or Git Bash / Linux (make).

CC     = gcc
CFLAGS = -Wall -g

# Tool and library paths differ on Windows vs Unix
ifeq ($(OS),Windows_NT)
  MINGW  = C:/MinGW/msys/1.0/bin
  export PATH := C:/MinGW/bin:$(PATH)
  FLEX   = $(MINGW)/flex.exe
  BISON  = $(MINGW)/bison.exe
  LDLIBS = -lfl -LC:/MinGW/msys/1.0/lib
else
  FLEX   = flex
  BISON  = bison
  LDLIBS = -lfl
endif

TARGET = myParser
SRCS   = parser.tab.c lexer.yy.c

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRCS) $(LDLIBS)

parser.tab.c parser.tab.h: parser.y
	$(BISON) -d parser.y

lexer.yy.c: lexer.l parser.tab.h
	$(FLEX) -o lexer.yy.c lexer.l

clean:
	rm -f $(TARGET) parser.tab.c parser.tab.h lexer.yy.c
