#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int volume;
char volume_icon[15], *dots[3];

pid_t pid = 0;
int pipefd[4];
FILE *pipe_output;
int status;

int main(int argc, char *argv[])
{
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
	pipe_output = fdopen(pipefd[2], "r");

	if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
		err_ret("fgets error: volume", errno);

	volume = (int) strtol(cmdout, NULL, 0);

	waitpid(pid, &status, 0);

	// Conditional Volume 'dots' Assignments
	if (volume > 0) {
		dots[0] = DOT;
		if (volume > 33) {
			dots[1] = DOT;
			if (volume > 66) {
				if (volume == 100) {
					dots[0] = STAR;
					dots[1] = STAR;
					dots[2] = STAR;
				} else {
					dots[2] = DOT;
				}
			} else {
				dots[2] = EDOT;
			}
		} else {
			dots[1] = EDOT;
			dots[2] = EDOT;
		}
	} else {
		dots[0] = EDOT;
		dots[1] = EDOT;
		dots[2] = EDOT;
	}


	if (snprintf(volume_icon, 15, "V%s%s%s  \n", dots[0], dots[1], dots[2]) == 0)
		fprintf(stderr, "volume: snprintf error");

	write_fifo(volume_icon);
	fclose(pipe_output);
	
	return 0;
}

