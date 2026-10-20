# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section

word1: .word 0xffcf4567
word2: .word 0xe7894599
save: .space 8

#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
    
main:                # Execution starts here

	lw t1, word1
	lw t2, word2
	add t3, t1, t2
	
	xor t4, t1, t2
	bgez t4, omoshmoi
	j nooverflow
	
omoshmoi:
	xor t5, t1, t3
	bgtz t5, overflow
	j nooverflow
		
overflow:
	addi a0, x0, 0xffffffff
	j end
	
nooverflow:
	j end

end:	sw t3, save, t0
	li    a7, 10     # Done, terminate program
    	ecall            # au revoir...

#----------------------- End of File ---------------------#
