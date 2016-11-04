/*
 * simulate.c
 *
 * Implement your (parallel) simulation here!
 */

#include <stdio.h>
#include <stdlib.h>

#include "simulate.h"


/* Add any global variables you may need. */


/* Add any functions you may need (like a worker) here. */


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
    point_per_thread = i_max / num_threads;

    // maken van threads
    pthread_t p_threads[num_threads];
    for(int i = 0; i < num_threads; i++) {
        pthread_create( &p_threads[i], NULL , &timesteps , t_max);
    }

    //kill threads
    for(int i = 0; i < num_threads; i++) {
        pthread_join( &p_threads[i], NULL );
    }

    // synchronizeer alle buffers and wait wait wait wait wait

    /*
     * After each timestep, you should swap the buffers around. Watch out none
     * of the threads actually use the buffers at that time.
     */

    int* temp1;
    temp1 = *current_array;
    *current_array = *next_array;
    *next_array = *old_array;
    *old_array = *temp1;

    // voer het opnieuw uit if t < t_max


    // close the program, write the end result to a file.
     /* You should return a pointer to the array with the final results. */
    return current_array;
}

/* Set a timestep */
void timesteps(steps) {
        // voer de formule uit
}
