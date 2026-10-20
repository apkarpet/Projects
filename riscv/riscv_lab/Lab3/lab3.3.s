# Name and general description of the program

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
	
alow: .word 0xffffffff
ahigh: .word 0x7fffffff
blow: .word 0x00000001
bhigh: .word 0x00000000

slow: .word 0
shigh: .word 0

		
#---------------------- text segment ---------------------#

    .text            # Program code goes in this section
    .globl main
main:                # Execution starts here

	la t0, alow
	lw x18, 0(t0)
	lw x19, 4(t0)
	
	la t1, blow
	lw x20, 0(t1)
	lw x21, 4(t1)
	
	add x7, x18, x20	# add low
	
	srli t3, x18, 31	#a31
	srli t4, x20, 31	#b31
	srli t5, x7, 31	#s31
	
	xori t6, t5, 1	#not s31
	
	and a0, t3, t4
	and a1, t6, t3
	and a2, t6, t4
	
	or a3, a0, a1
	or x22, a3, a2	#cout in x22
	
	add x8, x19, x21	#add high
	add x8, x8, x22		#add cout to high
	
	la x26, slow
	sw x7, 0(x26)
	sw x8, 4(x26)
	
	li a7, 10
	ecall
	
