/* Martijn Dortmond en Danyllo Verweij
* Calculating the wave equation over a number of time steps using MPI.
* The wave is divided into several parts, each which calculates a part of the wave equation.
* To calculate the full wave the first and last point need to be communicated with the
* previous and next mpi-process.
*/

#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <string.h>

#include "simulate.h"

/*
 * i_max: how many data points are on a single wave
 * t_max: how many iterations the simulation should run
 * old_array: array of size i_max filled with data for t-1
 * current_array: array of size i_max filled with data for t
 * next_array: array of size i_max. You should fill this with t+1
 */
double *simulate(const int i_max, const int t_max, double *old_array,
        double *current_array, double *next_array)
{

     MPI_Request request1[2], request3[2], request2[4];

     MPI_Status  status,status1[2],status3[2],status2[4];

     double *old_chunk, *current_chunk, *next_chunk;
     int num_tasks, my_rank;

     MPI_Comm_size( MPI_COMM_WORLD , & num_tasks ); // Get num tasks
     MPI_Comm_rank( MPI_COMM_WORLD , & my_rank ); // Get task id

     /* Calculate the amount of work for each proces. */
     int chunk_size = (int) i_max / num_tasks;
     /* Get the number of the right and left neibgor. */
     int left = my_rank - 1;
     int right = my_rank + 1;

     /* Locate a buffer for each proces. */
     old_chunk = malloc((chunk_size + 2) * sizeof(double));
     current_chunk = malloc((chunk_size + 2) * sizeof(double));
     next_chunk = malloc((chunk_size + 2) * sizeof(double));

     if (old_chunk == NULL || current_chunk == NULL || next_chunk == NULL) {
        fprintf(stderr, "Could not allocate enough memory, aborting.\n");
        return 0;
    }

    memset(old_chunk, 0, (chunk_size + 2) * sizeof(double));
    memset(current_chunk, 0, (chunk_size + 2) * sizeof(double));
    memset(next_chunk, 0, (chunk_size + 2) * sizeof(double));


    /* The master chunck divides the data among all processes.*/
     if (my_rank == 0) {
         for (int i = my_rank + 1; i < num_tasks; i++) {
             for(int a = 1; a < chunk_size + 1; a++) {
                 old_chunk[a] = old_array[a + (i * chunk_size)];
                 current_chunk[a] = current_array[a + (i * chunk_size)];
             }
             MPI_Send(old_chunk, chunk_size + 2, MPI_DOUBLE, i, i, MPI_COMM_WORLD);
             MPI_Send(current_chunk, chunk_size + 2, MPI_DOUBLE, i, i, MPI_COMM_WORLD);
         }
         for(int a = 1; a < chunk_size + 1; a++) {
             old_chunk[a] = old_array[a];
             current_chunk[a] = current_array[a];
         }
     } else {
         MPI_Recv(old_chunk, chunk_size + 2, MPI_DOUBLE, 0, my_rank, MPI_COMM_WORLD,&status);
         MPI_Recv(current_chunk, chunk_size + 2, MPI_DOUBLE, 0, my_rank, MPI_COMM_WORLD,&status);
     }
     printf( "right,%d, left %d, process %d", right,left, my_rank);


     for (int t = 0; t < t_max; t++) {
        if (my_rank == 0) {
            MPI_Irecv(&current_chunk[chunk_size + 1], 1, MPI_DOUBLE, right, 1, MPI_COMM_WORLD,&request1[0]);
            MPI_Isend(&current_chunk[chunk_size], 1, MPI_DOUBLE, right, 1, MPI_COMM_WORLD, &request1[1]);
        }
        else if (my_rank == num_tasks - 1) {
            MPI_Irecv(&current_chunk[0], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD,&request3[0]);
            MPI_Isend(&current_chunk[1], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD,&request3[1]);
        }
        else {
            MPI_Irecv(&current_chunk[chunk_size + 1], 1, MPI_DOUBLE, right, 1, MPI_COMM_WORLD, &request2[0]);
            MPI_Isend(&current_chunk[chunk_size], 1, MPI_DOUBLE, right, 1, MPI_COMM_WORLD,&request2[1]);

            MPI_Irecv(&current_chunk[0], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD,&request2[2]);
            MPI_Isend(&current_chunk[1], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD,&request2[3]);
        }
        for (int j = 2; j < chunk_size; j++) {
            next_chunk[j] = 2 * current_chunk[j] - old_chunk[j] + 0.15 * (current_chunk[j - 1] - (2 * current_chunk[j] - current_chunk[j + 1]));
        }

        if (my_rank == num_tasks -1) {
            MPI_Waitall(2,request3,status3);
            next_chunk[1] = 2 * current_chunk[1] - old_chunk[1] + 0.15 * (current_chunk[0] - (2 * current_chunk[1] - current_chunk[2]));
        }
        else if (my_rank == 0) {
            MPI_Waitall(2,request1,status1);
            next_chunk[chunk_size + 1] = 2 * current_chunk[chunk_size + 1] - old_chunk[chunk_size + 1] + 0.15 * (current_chunk[chunk_size ]
                           - (2 * current_chunk[chunk_size + 1] - current_chunk[chunk_size + 2]));
        }
        else {
            MPI_Waitall(4,request2,status2);
            next_chunk[1] = 2 * current_chunk[1] - old_chunk[1] + 0.15 * (current_chunk[0] - (2 * current_chunk[1] - current_chunk[2]));
            next_chunk[chunk_size + 1] = 2 * current_chunk[chunk_size + 1] - old_chunk[chunk_size + 1] + 0.15 * (current_chunk[chunk_size ]
                           - (2 * current_chunk[chunk_size + 1] - current_chunk[chunk_size + 2]));
        }

        double* temp = old_chunk;
        old_chunk = current_chunk;
        current_chunk = next_chunk;
        next_chunk = temp;
     }

     if(my_rank == 0 ) {
         double temp[chunk_size + 2]

     }


    MPI_Finalize();
    /* You should return a pointer to the array with the final results. */
    return current_array;
}
