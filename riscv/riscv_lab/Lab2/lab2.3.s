# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
	
	msg: .asciz "Enter a string: "
	msg2: .asciz "You entered: "

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	li a0, 31	
	li a7, 9	#sbrk
	ecall	

	add t0, a0, x0

	la a0, msg	#print msg
	li a7, 4
	ecall 
	
	add a0, t0, x0
	li a1, 31	#read string
	li a7, 8
	ecall
	
	la a0, msg2	#print msg2
	li a7, 4
	ecall
	
	sb x0, 5(t0)	#cut string to first 5 chars
	
	add a0, t0, x0	#print string (first 5 chars)
	li a7, 4
	ecall
	
	li a7, 10
	ecall
	