/*
 * simulate.c
 *
 * Implement your (parallel) simulation here!
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include  <pthread.h>
#include "simulate.h"

pthread_cond_t count;
pthread_mutex_t count_mutex;

struct parameters {
int counter;
int simulationtime;
double* old;
double* current;
double* next;
}params;

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

    params.counter = 0;
    params.simulationtime = t_max;
    params.old = old_array;
    params.current = current_array;
    params.next = next_array;

    pthread_t  thread_ids[num_threads];
    pthread_mutex_init(&count_mutex, NULL);
    pthread_cond_init (&count, NULL);

    //void *result;
    for (int i = 0; i < num_threads; i++) {
        int point_per_thread = i * i_max / num_threads;
        pthread_create( &thread_ids[i], NULL ,&HelloWorld , &point_per_thread);
    }

    for(int i = 0; i < t_max; i++) {
        /* wait till all threads are finished the timestep */
        while (params.counter < num_threads) {
            sleep (1);
        }
        /* swap the buffers around */
        double* temp1;
        temp1 = params.current;
        params.current = params.next;
        params.next = params.old;
        params.old = temp1;

        /* broadcast that next step needs to be taken. */
        pthread_mutex_lock(&count_mutex);
        printf("gonna broadcast now\n");
        pthread_cond_broadcast(&count);
        pthread_mutex_unlock(&count_mutex);
        params.counter = 0;
    }


    for (int i = 0; i < num_threads; i++) {
        pthread_join( thread_ids[i], NULL );
        //free( result );
    }


    // close the program, write the end result to a file.
     /* You should return a pointer to the array with the final results. */
    return params.current;
}

void *HelloWorld(void *args) {
    int* maxi = (int*) args;
    for (int i = 0; i < params.simulationtime; i++) {
        /* bereken en wacht op volgende stap ( nu ff printen dit is een thread) */
            const int c = 0.15;
            for(int i = 0; i < *maxi; i++) {
                int nexti, previousi;
                double eqone = 2 * (params.current[i] - params.old[i]);
                if(i - 1 < 0) {
                    previousi = 0;
                } else {
                    previousi = params.current[i - 1];
                }
                if (i + 1 >= *maxi) {
                    nexti = 0;
                } else {
                    nexti = params.current[i + 1];
                }
                double eqtwo = c * (previousi - 2 * (params.current[i] - nexti));
                params.next[i] = eqone + eqtwo;
                printf("%f", params.next[i]);
            }

        /* Show the main thread that you fisnished this time step. */
        params.counter += 1;
        /* Wait for the message that all threas are finshed.*/
        pthread_mutex_lock(&count_mutex);
        pthread_cond_wait(&count, &count_mutex);
        pthread_mutex_unlock(&count_mutex);
    }
}
