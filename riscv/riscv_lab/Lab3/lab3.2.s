# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
	
a:	.word 0xffffffff
b:	.word 0x00000001


#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	la x10, a
	lw x5, 0(x10)
	
	la x11, b
	lw x6, 0(x11)
	
	add x7, x5, x6
	
	srli x12, x5, 31	#a31
	srli x13, x6, 31	#b31
	srli x14, x7, 31	#s31
	
	xori x15, x14, 1	#not s31
	
	and x16, x12, x13
	and x17, x15, x12
	and x18, x15, x13
	
	or x19, x16, x17
	or x19, x19, x18	#cout in x19
	
	
	li a7, 10
	ecall
	
