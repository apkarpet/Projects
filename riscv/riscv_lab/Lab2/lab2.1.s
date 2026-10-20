# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
	
	msg1: .asciz "Enter a number: "
	msg2: .asciz "You entered: "

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	la a0, msg1	#PrintString
	li a7, 4
	ecall

	li a7, 5	#ReadInt
	ecall
	add t0, x0, a0
	
	la a0, msg2	#PrintString (2)
	li a7, 4
	ecall
	
	add a0, x0, t0	#PrintInt
	li a7, 1
	ecall            # au revoir...

#----------------------- End of File ---------------------#
