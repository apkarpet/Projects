# lab11-2.s
################################################################
# a0 = vectorsize (number of elements, NOT bytes)
# a1 = stepsize (number of elements)
# a2 = repcount
# a3 = option (0 or 1)
################################################################

#---------------------- data segment ---------------------#
    .data
vec: .word 256   # reserve some space for the vector (example: 256 bytes = 64 elements)


#---------------------- text segment ---------------------#
    .text
    .globl main
main:
#=========================================================#
    li	 a0, 32		            # vector size in elements (power of 2 < vectorsize)
	li	 a1, 8		            # step size  (power of 2 > 0)
	li	 a2, 8		            # rep count  (int > 0)
	li	 a3, 0		            # 0 = option 0, 1 = option 1
#=========================================================#

    la   t3, vec                # t3 = base address of vector
    li   t0, 0                  # k = 0

outer_loop:
    bge  t0, a2, done           # if (k >= repcount) exit
    addi t1, t0, 0              # index = k

inner_loop:
    bge  t1, a0, next_k         # if (index >= vectorsize) go to next k

    # address = &vector[index] = base + index*4
    slli t2, t1, 2              # t2 = index * 4 (bytes)
    add  t2, t3, t2             # t2 = base + index*4
    beq  a3, x0, option0        # if(option == 0) go to option0

    # Option 1: vector[index] = vector[index] + 1
    lw   t4, 0(t2)              # load vector[index]
    addi t4, t4, 1              # +1
    sw   t4, 0(t2)              # store back
    jal  x0, step_and_continue

option0:
    # Option 0: vector[index] = 0
    sw   x0, 0(t2)              # store 0

step_and_continue:
    add  t1, t1, a1             # index += stepsize
    jal  x0, inner_loop

next_k:
    addi t0, t0, 1              # k++
    jal  x0, outer_loop

done:
	li	 a7, 10		            # Done, terminate program
	ecall                       # au revoir...