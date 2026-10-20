# lab10-1.s
# Fibonacci sequence 

#---------------------- data segment ---------------------#
    .data   
n:    .word 10                                    # Number of Fibonacci number to compute
fib:  .word 0, 1, 99, 99, 99, 99, 99, 99, 99, 99  # Store the Fibonacci sequence (initial values)


#---------------------- text segment ---------------------#

    .text             
    .globl main
main:                  
    la   a0, n          # Load address of 'n'
    lw   a1, 0(a0)      # Load the number of Fibonacci numbers to compute
    la   a2, fib        # Load address of the fib array
    li   t0, 2          # Initialize counter for Fibonacci sequence 
                        # (starting from the third number where the first result shoud be stored)

loop:
    bge  t0, a1, end    # If counter t0 >= n, exit loop
    lw   t1, 0(a2)      # Load fib[a2] (current Fibonacci number)
    lw   t2, 4(a2)      # Load fib[a2+1] (next Fibonacci number)
    add  t3, t1, t2     # Add the two previous numbers to get the current Fibonacci number
    sw   t3, 8(a2)      # Store fib[t0] in fib[a2]
    addi t0, t0, 1      # Increment the counter
    addi a2, a2, 4      # Move to the next storage location in the fib array
    jal  x0, loop       # Jump to the start of the loop

end:
    addi  a0, t3, 0     # Move the final number to a0 (preparing the PrintInt system call)
    li    a7, 1         # Move 1 to a7 (1 refers to PrintInt system call code)
    ecall               # PrintInt system call

    li    a7, 10        # Done, terminate program
    ecall               # au revoir...

#----------------------- End of File ---------------------#