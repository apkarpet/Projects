#include <stdio.h>

int main(void) {
    int k, index;

    int vectorsize = 64;   // number of elements in the vector
    int stepsize  = 8;     // step size (in elements)
    int repcount  = 8;     // how many times to repeat the outer loop
    int option    = 0;     // 0 => write 0, 1 => read+increment

    int vector[vectorsize];        // vectorsize elements, sizeof(int) == 4 assumed

    // Initialize vector so that option==1 does not read uninitialized data
    // This loop does not exit in RISC-V code
    for (index = 0; index < vectorsize; index++) {
        vector[index] = index;   // or any other initial value
    }

    for (k = 0; k < repcount; k++) {      // repeat repcount times
        /* Step through the selected vector segment with the given step size. */
        for (index = k; index < vectorsize; index += stepsize) {
            if (option == 0)
                vector[index] = 0;         // Option 0: one cache access - write
            else
                vector[index] = vector[index] + 1;  // Option 1: read + write
        }
    }

    return 0;
}