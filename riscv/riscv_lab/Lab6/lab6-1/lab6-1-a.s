# lab6-1-a.s

#---------------------- text segment ---------------------#

    .text
    .globl main
main:  
    li     x9, 0x100
    lw     x5, 0(x9)         # Error here: Runtime exception at 0x00400004: address out of range 0x00000100

    li     a7, 10            # Done, terminate program (exit 0)
    ecall                    # au revoir...

#----------------------- End of File ---------------------#