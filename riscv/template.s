# Program to read a string and truncate it to 5 characters

#---------------------- data segment ---------------------#
    .data   
msg:          .asciz "user input: "

myVector: .word 1, 2, 3, 4, 5
vecSum: .word 0

#---------------------- text segment ---------------------#
    .text            
    .globl main
main:                
	
	la t0, myVector
	
	addi t1, zero, 5
loop:
	beq t1, zero, end
	lw t2, 0(t0)
	
	add s0, s0, t2
	
	addi t0, t0, 4
	addi t1, t1, -1
	j loop
	
end:
	mv a0, s0
	li a7, 1
	ecall

    li    a7, 10     
    ecall

	
#----------------------- End of File ---------------------#