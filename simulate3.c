/*
 * simulate.c
 *
 * Implement your (parallel) simulation here!
 */

#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

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
 * old_array: array of size i_max filled with data for t-1
 * current_array: array of size i_max filled with data for t
 * next_array: array of size i_max. You should fill this with t+1
 */
double *simulate(const int i_max, const int t_max, double *old_array,
        double *current_array, double *next_array, int argc, char[] argv)
{

    /*
     * Your implementation should go here.
     */
	 
	 int rc, num_tasks, my_rank;
	 
	 rc = MPI_Init(&argc, &argv);
	 
	 if (rc != MPI_SUCCESS) {
		 fprintf ( stderr , " Unable to set up MPI ");
		 MPI_Abort ( MPI_COMM_WORLD , rc );
	 }
	 
	 MPI_Comm_size( MPI_COMM_WORLD , & num_tasks ); // Get num tasks
	 MPI_Comm_rank( MPI_COMM_WORLD , & my_rank ); // Get task id
	 
	 int chunk_size = (int) i_max / num_tasks;
	 
	 int left = my_rank - 1;
	 int right = my_rank + 1;
	 
	 double old_chunk = malloc((chunk_size + 2) * sizeof(double));
	 double current_chunk = malloc((chunk_size + 2) * sizeof(double));
	 double next_chunk = malloc((chunk_size + 2) * sizeof(double));
	 
	 if (old_chunk == NULL || current_chunk == NULL || next_chunk == NULL) {
        fprintf(stderr, "Could not allocate enough memory, aborting.\n");
        return EXIT_FAILURE;
    }
	
	memset(old_chunk, 0, (chunk_size + 2) * sizeof(double));
    memset(current_chunk, 0, (chunk_size + 2) * sizeof(double));
    memset(next_chunk, 0, (chunk_size + 2) * sizeof(double));
	 
	 if (my_rank == 0) {
		 for (int i = my_rank + 1; i < num_tasks; i++) {
			 for(int a = 1; a < chunk_size + 1; a++) {
				 old_chunk[a] = old_array[a + (i * chunk_size)];
				 current_chunk[a] = current_array[a + (i * chunk_size)];				 
			 }
			 MPI_Isend(&old_chunk, chunk_size + 2, MPI_DOUBLE, i, i, MPI_COMM_WORLD);
			 MPI_Isend(&current_chunk, chunk_size + 2, MPI_DOUBLE, i, i, MPI_COMM_WORLD);
		 }
		 for(int a = 1; a < chunk_size + 1; a++) {
			 old_chunk[a] = old_array[a];
			 current_chunk[a] = current_array[a];
		 }
	 } else {
		 MPI_Irecv(&old_chunk, chunk_size + 2; MPI_DOUBLE, 0, my_rank, MPI_COMM_WORLD);
		 MPI_Irecv(&current_chunk, chunk_size + 2; MPI_DOUBLE, 0, my_rank, MPI_COMM_WORLD);
	 }
	 
	 for (int t = 0; t < t_max; t++) {
		 if (my_rank == 0) {
			 MPI_Irecv(&current_chunk[chunk_size + 1], 1, MPI_DOUBLE, right, chunk_size + 1, MPI_COMM_WORLD);
			 MPI_Isend(&current_chunk[chunk_size], 1, MPI_DOUBLE, right, chunk_size, MPI_COMM_WORLD);
		 } else if (my_rank == num_tasks - 1) {
			 MPI_Irecv(&current_chunk[0], 1, MPI_DOUBLE, left, 0, MPI_COMM_WORLD);
			 MPI_Isend(&current_chunk[1], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD);
		 } else {
			 MPI_Irecv(&current_chunk[chunk_size + 1], 1, MPI_DOUBLE, right, chunk_size + 1, MPI_COMM_WORLD);
			 MPI_Isend(&current_chunk[chunk_size], 1, MPI_DOUBLE, right, chunk_size, MPI_COMM_WORLD);
			 
			 MPI_Irecv(&current_chunk[0], 1, MPI_DOUBLE, left, 0, MPI_COMM_WORLD);
			 MPI_Isend(&current_chunk[1], 1, MPI_DOUBLE, left, 1, MPI_COMM_WORLD);
		 }
		 for (int j = 1; j < chunk_size + 1; j++) {
			 new_chunk[j] = 2 * current_chunk[j] - old_chunk[j] + 0.15 * (current_chunk[j - 1] - (2 * current_chunk[j] - current_chunk[j + 1]));
		 }
		 double temp = old_chunk;
		 old_chunk = current_chunk;
		 current_chunk = next_chunk;
		 next_chunk = temp;
	 }
	 
	 
	 
	 

	 
	 
	MPI_Finalize();
    /* You should return a pointer to the array with the final results. */
    return current_array;
}

/*int main(int argc, char *argv[]) {
	
	int rc, num_tasks, my_rank;
	
	rc = MPI_Init(&argc, &argsv);
	
}*/
