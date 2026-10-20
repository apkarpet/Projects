# lab10-1-real.s
# Fibonacci sequence χωρίς ψευδοεντολές 

#---------------------- data segment ---------------------#
    .data   
n:    .word 10                                    # Number of Fibonacci number to compute
fib:  .word 0, 1, 99, 99, 99, 99, 99, 99, 99, 99  # Store the Fibonacci sequence (initial values)


#---------------------- text segment ---------------------#

# Αντικατάσταση της la a0, n 
lui a0, 0x10000
addi a0, a0, 0x000 

lw a1, 0(a0)

#αντικατασταση της la a2, fib 
lui a2, 0x10000 
addi a2, a2, 0x00c

#Αντικατάσταση της li t0, 2
addi t0, x0, 2

loop:
bge t0, a1, end 
lw t1, 0(a2)
lw t2, 4(a2)
add t3, t1, t2
sw t3, 8(a2)
addi t0, t0, 1 
addi a2, a2, 4 
jal x0, loop 

end:
addi a0, t3, 0 

#αντικατασταση της li a7, 1
addi a7, x0, 1 
ecall 

#Αντικατάσταση της li a7, 10 
addi a7, x0, 10 
ecall 

#----------------------- End of File ---------------------#
