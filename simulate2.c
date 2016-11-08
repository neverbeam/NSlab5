/*
 * simulate.c
 *
 * Implement your (parallel) simulation here!
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <omp.h>
#include "simulate.h"

/* Add any functions you may need (like a worker) here. */
void *HelloWorld(void *args);

/* function we want to complete */

/*
 * Executes the entire simulation.
 *
 * Implement your code here.
 *
 * i_max: how many data points are on a single wave
 * t_max: how many iterations the simulation should run
 * num_threads: how many threads to use (excluding the main threads)
 * old_array: array of size i_max filled with data for t-1
 * current_array: array of size i_max filled with data for t
 * next_array: array of size i_max. You should fill this with t+1
 */
double *simulate(const int i_max, const int t_max, const int num_threads,
        double *old_array, double *current_array, double *next_array)
{

    omp_set_num_threads(num_threads);

    /* bereken en wacht op volgende stap ( nu ff printen dit is een thread) */
    const double c = 0.15;
    for(int t = 0; t < t_max ; t++) {
        #pragma omp parralel for
        for(int i = 0; i < i_max ; i++) {
            int nexti, previousi;
            double eqone = 2 * current_array[i] - old_array[i];
            if(i - 1 < 0) {
                previousi = 0;
            } else {
                previousi = current_array[i - 1];
            }
            if (i + 1 >= i_max) {
                nexti = 0;
            } else {
                nexti = current_array[i + 1];
            }
            double eqtwo = c * (previousi - (2 * current_array[i] - nexti));
            next_array[i] = eqone + eqtwo;
            printf("%f", next_array[i]);
        }

        double* temp_array;
        temp_array = current_array;
        current_array = next_array;
        next_array = old_array;
        old_array = temp_array;
    }

    // close the program, write the end result to a file.
     /* You should return a pointer to the array with the final results. */
    return current_array;
}
