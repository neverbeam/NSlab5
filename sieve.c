/* Martijn Dortmond en Danyllo verweij
* 10740406 en 10770488
* Making the sieve of Eratosthenes using multiple threads to look for prime numbers.
* The main thread create an infinit amount of natural numbers and passes them to the
* first thread with primenumber 2. When the modulo of the thread primenumber with the
* natural number is 0 it is thrown away because it is not a prime number. When it is not 0
* it passes it to the next thread. If this is the first time it passes a number to the next thread
* it makes a new thread with the thread primenumber the current natural number. This number
* is a new prime number.
*
*/
#include <unistd.h>
#include <stdio.h>
#include  <pthread.h>
#include "timer.h"


#define buffersize 10

double priemnumbersfound = 0;

/* Parameters to pass to the next thread. We need to pass the buffer and the value how
    much is currently in the buffer ( occupied). As well as the lock for this buffer
    and his priem number. */
struct parameters {
    double bufferout[buffersize];
    int occupied;
    int mypriem;
    pthread_mutex_t lockin;
};

/* sieve threads */
void *sieve(void* args) {
    priemnumbersfound += 1;
    pthread_mutex_t lockout;
    pthread_mutex_init(&lockout, NULL);
    pthread_t thread_ids;

    struct parameters paraout;
    struct parameters* parain = args;
    /* Grab all the parameters from the given struct. */
    double* bufferin = parain->bufferout;
    int* occupied = &(parain->occupied);
    int mynumber = parain->mypriem;
    pthread_mutex_t lockin = parain->lockin;

    int val;
    int nextin = 0, nextout = 0;
    int done;
    int gotoutputbuffer = 1;

    /* Print your own priem number. */
    printf("Een nieuwe priemgetal: %d \n", mynumber);

    /* Keep on looping until termination. */
    while(1) {
        /* Loop untill sometill has been put in the buffer and then read it. */
        done = 0;
        while(!done) {
            /* Lock the intput buffer */
            pthread_mutex_lock(&lockin);
            /* If there is something in the buffer. */
            if (*occupied > 0) {
                val = bufferin[nextin];
                //printf( "got val %d in thread %d\n", val,mynumber);
                /* Slide to the next value. */
                nextin += 1;
                /* If the slide is at the end of the buffer return to the begin. */
                if (nextin == buffersize) {
                    nextin = 0;
                }
                /* Change the size of elements currently in the buffer. */
                *occupied -= 1;
                done = 1;
            }
            pthread_mutex_unlock(&lockin);
        }

        /* As long as the number has not been sieved yet. */
        //printf("checking val %d in thread %d\n", val , mynumber);
        sleep(0);
        if( val % mynumber != 0) {
            //printf( "received %d in thread %d\n", val,mynumber);
            /* if the output buffer does not exist, create one. */
            if (gotoutputbuffer) {
                paraout.occupied = 0;
                paraout.mypriem = val;
                paraout.lockin = lockout;
                pthread_create(&thread_ids,NULL,&sieve, &paraout);
                gotoutputbuffer = 0;
            }
            /* Pass the number to the next thread. */
            else {
                done = 0;
                /* Loop untill you are able to write in the buffer. */
                while(!done){
                    pthread_mutex_lock(&lockout);
                    /* Check wether the buffer is writeable */
                    if(paraout.occupied < buffersize) {
                        paraout.bufferout[nextout] = val;
                        nextout += 1;
                        if (nextout == buffersize) {
                            nextout = 0;
                        }
                        paraout.occupied += 1;
                        done = 1;
                    }
                    pthread_mutex_unlock(&lockout);
                }
            }
        }
    }
}

/* main thread starting the sieve. */
int main() {
    timer_start();
    pthread_t thread_ids;
    pthread_mutex_t lockout;
    pthread_mutex_init(&lockout, NULL);

    /* create the parameters for the first sieve. */
    struct parameters params;
    params.occupied = 0;
    params.mypriem = 2;
    params.lockin = lockout;
    int nextins = 0;
    pthread_create(&thread_ids,NULL,&sieve, &params);

    /* Start with natural number 2 and keep on giving new natural numbers untill
        termination of the user.*/
    int i = 2;
    while(1){
        if(priemnumbersfound == 100) {
            double time = timer_end();
            printf("took %g seconds", time);
        }
        /* Check wether you are able to write in the buffer. */
        if (params.occupied < buffersize) {
            pthread_mutex_lock(&lockout);
            params.bufferout[nextins] = i;
            params.occupied += 1;
            pthread_mutex_unlock(&lockout);
            nextins += 1;
            if (nextins == buffersize) {
                nextins = 0;
            }
            sleep(0);
            i++;
        }
    }
    pthread_join(thread_ids,NULL);
}
