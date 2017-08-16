#include <sys/stat.h>
#include <sys/resource.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>

void
daemonize(const char *cmd)
{
	int pid, fd0, fd1, fd2;
	struct rlimit rl;
	umask(0);

	if (getrlimit(RLIMIT_NOFILE, &rl) < 0)
		perror(cmd);

	if ((pid = fork()) < 0)
		perror(cmd);
	else if (pid > 0)
		exit(0);
	setsid();

	if (chdir("/") < 0)
		perror(cmd);

	if (rl.rlim_max == RLIM_INFINITY)
		rl.rlim_max = 1024;
	for (int i = 0; i < rl.rlim_max; ++i) {
		close(i);
	}
    fd0 = open("/dev/null", O_RDWR);
    fd1 = dup(0);
    fd2 = dup(0);
}
