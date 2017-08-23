#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <sys/wait.h>
#include "errorwraps.h"

#define OFLAGS O_RDWR | O_CREAT
#define OMODE S_IRUSR | S_IWUSR
#define MAXARG 256

static int fd;

void exith(void);
void sighand(int);

int main(int argc, char *argv[])
{
	// ----- Exit and Signal Handling -----
	if (atexit(exith) != 0)
		err_sys("atexit");

	struct sigaction sa;
	sigset_t mask;
	sigemptyset(&mask);

	sa.sa_handler = sighand;
	sa.sa_mask = mask;

	if (sigaction(SIGTERM, &sa, NULL) < 0)
		log_sys("sigaction");
	if (sigaction(SIGINT, &sa, NULL) < 0)
		log_sys("sigaction");
	if (sigaction(SIGQUIT, &sa, NULL) < 0)
		log_sys("sigaction");

	// ----- Command Line Arguments -----
	int c;
	char *cmd, *lockfile;
	while ((c = getopt(argc, argv, "c:f:")) != -1) {
		switch (c) {
			case 'c':
				cmd = optarg;
				break;
			case 'f':
				lockfile = optarg;
				break;
			default:
				abort();
		}
	}

	// ----- Splitting 'cmd' into 'cmdv' -----
	int count = 2; // one for command name; one for null ptr at the end
	char *cmdp = cmd;
	int cmd_len = strlen(cmd);
	for (int i = 0; i < cmd_len; i++) {
		if (*cmdp++ == ' ') {
			count++;
		}
	}

	char **cmdv = malloc(sizeof(char *) * count);

	cmdv[0] = strtok(cmd, " ");
	for (int i = 1; i < count; ++i) {
		cmdv[i] = strtok(NULL, " ");
	}


	// ----- File Locking -----
	fd = open(lockfile, OFLAGS, OMODE);
	if (fd < 0)
		err_sys("open");

	if (lockf(fd, F_LOCK, 0) < 0)
		err_sys("lockf (lock)");

	// ----- Spawning 'cmd' -----
	pid_t pid;
	if ((pid = fork()) < 0)
		err_sys("fork");
	else if (pid == 0) {
		execvp(cmdv[0], cmdv); 
	}

	free(cmdv);

	int status;
	waitpid(pid, &status, 0);
	if (status != 0)
		err_quit("status = %d", status);

	exit(0);
}

void
exith(void)
{
	if (lockf(fd, F_ULOCK, 0) < 0)
		err_sys("lockf (ulock)");

	close(fd);
}

void
sighand(int signo)
{
	exit(1);
}
