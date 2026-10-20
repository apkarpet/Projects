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
    li a5, 0
    
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
    add   a0, x0, a2
    add   a1, x0, a2

    # Find the minimum value
    blt   a3, a0, a3min
    jal   x0, check_c

a3min:
    add   a0, x0, a3       # the second number is the new minimum

check_c:
    blt   a4, a0, a4min
    jal   x0, check_d

a4min:
    add   a0, x0, a4       # the third number is the new minimum

check_d:
    blt   a5, a0, a5min
    jal   x0, find_max

a5min:
    add   a0, x0, a5       # the forth number is the new minimum

find_max:
    # Find the maximum value
    bgt   a3, a1, a3max
    jal   x0, check_c_max

a3max:
    add   a1, x0, a3       # the second number is the new maximum

check_c_max:
    bgt   a4, a1, a4max
    jal   x0, check_d_max

a4max:
    add   a1, x0, a4       # the third number is the new maximum

check_d_max:
    bgt   a5, a1, a5max
    jal   x0, end_proc

a5max:
    add   a1, x0, a5       # the forth number is the new maximum

end_proc:
    jalr  x0, 0(ra)

#----------------------- End of File ---------------------#
