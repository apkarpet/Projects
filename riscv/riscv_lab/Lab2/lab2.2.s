# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
	
	msg1: .asciz "Enter a number: "
	sum: .asciz "Sum of numbers =  "
	diff: .asciz "Difference of numbers =  "
	nl: .asciz "\n"

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here
	
	la a0, msg1	#msg1
	li a7, 4
	ecall
	
	li a7, 5	#readInt (1)
	ecall
	add t0, x0, a0
	
	la a0, msg1	#msg1
	li a7, 4
	ecall
	
	li a7, 5	#readInt (2)
	ecall
	add t1, x0, a0
	
	add t2, t1, t0	#add
	sub t3, t1, t0	#sub
	
	la a0, sum
	li a7, 4
	ecall
	
	add a0, x0, t2
	li a7, 1
	ecall
	
	la a0, nl
	li a7, 4
	ecall
	
	la a0, diff
	li a7, 4
	ecall
	
	add a0, x0, t3
	li a7, 1
	ecall

#----------------------- End of File ---------------------#
