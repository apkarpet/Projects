# lab4-1.s

#---------------------- data segment ---------------------#

    .data   # Data declarations go in this section
msg_min: .asciz "The smallest number is: "
msg_max: .asciz "The largest number is: "

#---------------------- text segment ---------------------#
    .text
    .globl main
main:

    # Load integers to registers 
    li a2, 5
    li a3, 10
    li a4, 15
    li a5, 20
    
    # Call the procedure proc
    jal   ra, proc
    
    addi  t0, a0, 0

    # Print the smallest number
    la    a0, msg_min     # Load address of msg_min
    li    a7, 4           # syscall to print string
    ecall

    addi  a0, t0, 0     # Move the smallest number to a1 for printing
    li    a7, 1           # syscall to print integer
    ecall

    # Print a new line
    li    a0, 10          # ASCII for newline
    li    a7, 11          # syscall to print character
    ecall

    # Print the largest number
    la    a0, msg_max     # Load address of msg_max
    li    a7, 4           # syscall to print string
    ecall

    addi  a0, a1, 0     # The largest number is already in a1
    li    a7, 1           # syscall to print integer
    ecall

    # Exit the program
    li    a7, 10
    ecall

proc:
    # push to stack
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    sw s1, 4(sp)
    
    add   s0, x0, a2
    add   s1, x0, a2

    # Find the minimum value
    blt   a3, s0, a3min
    jal   x0, check_c

a3min:
    add   s0, x0, a3       # the second number is the new minimum

check_c:
    blt   a4, s0, a4min
    jal   x0, check_d

a4min:
    add   s0, x0, a4       # the third number is the new minimum

check_d:
    blt   a5, s0, a5min
    jal   x0, find_max

a5min:
    add   s0, x0, a5       # the forth number is the new minimum

find_max:
    # Find the maximum value
    bgt   a3, s1, a3max
    jal   x0, check_c_max

a3max:
    add   s1, x0, a3       # the second number is the new maximum

check_c_max:
    bgt   a4, s1, a4max
    jal   x0, check_d_max

a4max:
    add   s1, x0, a4       # the third number is the new maximum

check_d_max:
    bgt   a5, s1, a5max
    jal   x0, end_proc

a5max:
    add   s1, x0, a5       # the forth number is the new maximum

end_proc:
    add   a0, x0, s0
    add   a1, x0, s1
    
    # pop from stack
    lw s1, 4(sp)
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    
    jalr  x0, 0(ra)

#----------------------- End of File ---------------------#
