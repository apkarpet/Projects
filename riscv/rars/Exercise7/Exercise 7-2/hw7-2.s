# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
ftemps: .float 18.5, 21.0, 19.5, 22.3, 20.0
five:   .float 5.0
save:   .space 4

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	la t0, ftemps
	li t1, 5
	
	fmv.w.x ft0, x0
	fmv.w.x ft1, x0
loop:
	beq t1, x0, done
	
	flw ft1, 0(t0)
	fadd.s ft0, ft0, ft1
	
	addi t0, t0, 4
	addi t1, t1, -1
	j loop

 done:
	la t2, five       
	flw ft2, 0(t2)       
	  
	fdiv.s ft0, ft0, ft2
	
	li a7, 10     # Done, terminate program
	ecall            # au revoir...

#----------------------- End of File ---------------------#
