# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section

input: .asciz "HelLO, wOrLd!"
output: .space 80

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	la t0, input
	la t4, output
	
loop:
	lbu t1, 0(t0)
	beq t1, x0, done
	
	li t2, 97	#'a'
	li t3, 122	#'z'
	
	#έλεγχος αν προκειται για Lowercase 
	blt t1, t2, skip	
	bgt t1, t3, skip
	
	addi t1, t1, -32	#μετατροπή lowercase to uppercase
	
skip:
	sb t1, 0(t4)	#store character
	addi t0, t0, 1
	addi t4, t4, 1
	j loop
done:
	sb x0, 0(t4)
	li    a7, 10     # Done, terminate program
    	ecall            # au revoir...

#----------------------- End of File ---------------------#
