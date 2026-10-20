# lab6-1-c.s

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
msg1:       .asciz "Exception with cause "
msg2:       .asciz " due to "
msg3:       .asciz " occured at address "

ermsg1:     .asciz "Load access fault"        # (ucause code: 5)
ermsg2:     .asciz "Load address misaligned"  # (ucause code: 4)
ermsg3:     .asciz "Illegal instruction"      # (ucause code: 2)


#---------------------- text segment ---------------------#
    .text
    .globl main
main:
    csrsi  ustatus, 1        # Set interrupt enable (instr: csrrsi x0, ustatus, 1)
    la     t0, exception_handler  # t0 <-- trap handler address
    csrw   t0, utvec         # Set utvec with trap handler address (instr: csrrw x0, utvec, t0)

    li     x9, 0x100       
    lw     x5, 0(x9)         # Exception due to Load access fault (ucause code: 5)
    
    li     a7, 10            # Done, terminate program (exit 0)
    ecall                    # au revoir...

exception_handler:

	# ------->
	# Write the Trap Handler code here......
	# <-------


#----------------------- End of File ---------------------#