# lab4-1.s

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
initx: 	.word 25
inity: 	.word 13
uninitz:.space 4
#---------------------- text segment ---------------------#
    .text
    .globl main
main:
	
	la t1, initx
	lw a1, 0(s1)
	
	la t2, inity
	lw a2, 0(t2)
	
	jal ra, sumIt
	
	la t0, uninitz
	sw a0, 0(t0)

	li a7, 10
	ecall
	
sumIt:
	
	addi sp, sp, -16
	sw ra, 12(sp)
	sw s0, 8(sp)
	sw s1, 4(sp)
	
	addi s0, x0, a1
	
	
	jal x0, sumItAgain
	addi s1, a0, a1
	
	lw s1, 4(sp)
	lw s0, 8(sp)
	lw ra, 12(sp)
	addi sp, sp, 16
	jalr x0, 0(ra)
	
sumItAgain:	
	addi a0, a2, 10
	jalr x0, 0(ra)
	
#----------------------- End of File ---------------------#
