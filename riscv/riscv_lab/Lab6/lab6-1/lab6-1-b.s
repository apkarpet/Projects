# lab6-1-b.s

#---------------------- text segment ---------------------#

    .text
    .globl main
main:
    csrsi  ustatus, 1        # Set interrupt enable (instr: csrrsi x0, ustatus, 1)
    la     t0, exception_handler  # t0 <-- trap handler address
    csrw   t0, utvec         # Set utvec with trap handler address (instr: csrrw x0, utvec, t0)

    li     x9, 0x100       
    lw     x5, 0(x9)         # Exception due to Load access fault (ucause code: 5)
    #lw    x5, 3(x0)         # Exception due to Load address misaligned (ucause code: 4)
    #csrrs x5, 1024, x0      # Exception due to Illegal instruction (uninitialized csr 1024, ucause code: 2)
    
    li     a7, 10            # Done, terminate program (exit 0)
    ecall                    # au revoir...

exception_handler:
    csrc   x0, ucause         # Clear ucause register (instr: csrrw a0, ucause, x0)  
    la     t0, end
    csrw   t0, uepc           # Move epc to success and return (instr: csrrw x0, uepc, t0)
    uret

end:
    li     a0, -1
    li     a7, 93             # Done, terminate program with code
    ecall                     # exit -1 (with errors)


#----------------------- End of File ---------------------#