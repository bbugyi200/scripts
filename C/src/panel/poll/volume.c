#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>
#include "A.h"


#define NUM_OF_DOTS 5
#define VOL_ICON_MAX 25


void err_ret(char *, int);
void write_fifo(char *);


int main(int argc, char *argv[])
{
	errno = 0;

	set_fifo();

	int volume;
	char volume_icon[VOL_ICON_MAX], *dots[NUM_OF_DOTS];

	pid_t pid = 0;
	int pipefd[4];
	FILE *pipe_output;
	int status;

	char *icon, cmdout[MAX_CMD];

	// First Pipe CMD
	pipe(pipefd);
	pid = fork();
	if (pid == 0) {
		dup2(pipefd[1], STDOUT_FILENO);
		execl("/usr/bin/amixer", "amixer", "get", "Master", (char *) NULL);
	}

	close(pipefd[1]);
	waitpid(pid, &status, 0);

	// Second Pipe CMD
	pipe(pipefd + 2);
	pid = fork();
	char *sed_pttrn = "s/^.*\\[\\([0-9]\\+\\)%.*$/\\1/p";
	if (pid == 0) {
		close(pipefd[2]);
		dup2(pipefd[0], STDIN_FILENO);
		dup2(pipefd[3], STDOUT_FILENO);
		execl("/usr/bin/sed", "sed", "-n", sed_pttrn, (char *) NULL);
	}

	close(pipefd[0]);
	close(pipefd[3]);
	waitpid(pid, &status, 0);

	pipe_output = fdopen(pipefd[2], "r");

	if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
		err_ret("fgets error: volume", errno);

	volume = (int) strtol(cmdout, NULL, 0);


	int bin_size = 100 / NUM_OF_DOTS;
	if (volume == 100) {
		for (int i = 0; i < NUM_OF_DOTS; i++) {
			dots[i] = STAR;
		}
	} else {
		for (int i = 0; i < NUM_OF_DOTS; i++) {
			if (volume > i*bin_size) {
				dots[i] = DOT;
			} else {
				dots[i] = EDOT;
			}
		}
	}

	if (snprintf(volume_icon, VOL_ICON_MAX, "V%s%s%s%s%s  \n", dots[0], dots[1], dots[2], dots[3], dots[4]) == 0)
		fprintf(stderr, "volume: snprintf error");

	write_fifo(volume_icon);
	fclose(pipe_output);
	
	return 0;
}
