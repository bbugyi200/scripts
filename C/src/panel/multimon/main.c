#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdbool.h>
#include "daemonize.h"
#include "errorwraps.h"
#include "../panel.h"
#include "bugyi.h"

void sighan(int);
void exith(void);

int main(int argc, char *argv[])
{
	// ----- Check pid File -----
	// Last chance to get printable output to the user.
	int fd = open(multimon_pid_path, OFLAGS, OMODE);

	if (fd < 0)
		log_sys("open");

	if (lockf(fd, F_TLOCK, 0) < 0) {
		fprintf(stderr, "%s\n", "multimon is already running!");
		_exit(1);
	}

	// ----- Daemonize -----
	daemonize(argv[0]);

	// ----- Signal Handlers -----
	atexit(exith);

	struct sigaction sa;
	sigset_t mask;
	sigemptyset(&mask);
	sa.sa_handler = sighan;
	sa.sa_mask = mask;

	if (sigaction(SIGTERM, &sa, NULL) < 0)
		log_sys("sigaction");
	if (sigaction(SIGINT, &sa, NULL) < 0)
		log_sys("sigaction");
	if (sigaction(SIGQUIT, &sa, NULL) < 0)
		log_sys("sigaction");

	// ----- Lock pid File -----
	// This must be redone because file descriptors are destroyed by the
	// daemonize function.
	fd = open(multimon_pid_path, OFLAGS, OMODE);

	if (fd < 0)
		log_sys("open");

	if (lockf(fd, F_TLOCK, 0) < 0) {
		syslog(LOG_ERR, "%s\n", "multimon is already running!");
		_exit(1);
	}

	// ----- Redirect stdin to 'bspc subsribe monitor' -----
	int pipefd[2];
	pid_t pid;
	if (pipe(pipefd) < 0)
		log_sys("pipe");
	if ((pid = fork()) < 0)
		log_sys("fork");
	else if (pid == 0) {
		close(pipefd[0]);
		dup2(pipefd[1], STDOUT_FILENO);
		execl("/usr/bin/bspc", "bspc", "subscribe", "monitor", (char *) NULL);
	}

	close(pipefd[1]);
	dup2(pipefd[0], STDIN_FILENO);

	// ----- Process 'bpsc subscribe monitor' output -----
	bool do_geometry;
	FILE *fp;
	char line[MAXLINE];
	while (fgets(line, MAXLINE, stdin) != NULL) {

		do_geometry = false;
		*strchr(line, '\n') = '\0';

		if ((strstr(line, "monitor_remove") != NULL) || (strstr(line, "monitor_add") != NULL)) {
			// ----- Get panel-init PID -----
			pid_t panel_pid;
			FILE *pid_fp = fopen(panel_pid_path, "r");

			if (fgets(line, MAXLINE, pid_fp) == NULL)
				err_sys("fgets");

			panel_pid = strtol(line, NULL, 0);

			do_geometry = true;
			kill(panel_pid, SIGTERM);

			// Ensures that panel-init is dead
			int fd = open(panel_pid_path, OFLAGS, OMODE);
			if (fd < 0)
				log_sys("open");
			if (lockf(fd, F_LOCK, 0) < 0)
				log_sys("lockf (lock)");
			if (lockf(fd, F_ULOCK, 0) < 0)
				log_sys("lockf (unlock)");

			// New instance of panel-init
			if ((pid = fork()) < 0)
				log_sys("fork (panel-init)");
			else if (pid == 0) {
				execl("/usr/local/bin/panel-init", "panel-init", (char *) NULL);
			}
		}

		if ((strstr(line, "monitor_geometry") != NULL) || do_geometry) {
			if ((pid = fork()) < 0)
				log_sys("fork");
			else if (pid == 0) {
				execl("/usr/local/bin/toggle_monitor", "toggle_monitor", (char *) NULL);
			}

			if (pipe(pipefd) < 0)
				log_sys("pipe");
			if ((pid = fork()) < 0)
				log_sys("fork");
			else if (pid == 0) {
				close(pipefd[0]);
				dup2(pipefd[1], STDOUT_FILENO);
				execl("/usr/bin/bspc", "bspc", "query", "-M", (char *) NULL);
			}

			int flags;
			flags = fcntl(pipefd[0], F_GETFL, 0);
			flags |= O_NONBLOCK;
			fcntl(pipefd[0], F_SETFL, flags);
			fp = fdopen(pipefd[0], "r");

			int num_of_monitors = 0, i = 0;
			char *monitors[2];
			usleep(250000);
			while (fgets(line, MAXLINE, fp) != NULL) {
				num_of_monitors++;
				*strchr(line, '\n') = '\0';
				monitors[i++] = line;
			}

			fclose(fp);


			if (num_of_monitors == 1) {
				if ((pid = fork()) < 0)
					log_sys("fork (bspc monitor -d)");
				else if (pid == 0) {
					execl("/usr/bin/bspc", "bspc", "monitor", "LVDS1", "-d", "I", "II", "III", "IV", "V", (char *) NULL);
				}
			} else if (num_of_monitors == 2) {
				if ((pid = fork()) < 0)
					log_sys("fork (bspc monitor -d)");
				else if (pid == 0) {
					execl("/usr/bin/bspc", "bspc", "monitor", monitors[0], "-d", "I", "II", "III", "IV", "V", (char *) NULL);
				}

				if ((pid = fork()) < 0)
					log_sys("fork (bspc monitor -d)");
				else if (pid == 0) {
					execl("/usr/bin/bspc", "bspc", "monitor", monitors[1], "-d", "VI", "VII", "VIII", "IX", "X", (char *) NULL);
				}
			} else {
				log_ret("num_of_monitors = %d", num_of_monitors);
			}
		}
	}
	
	return 0;
}

void
sighan(int signo)
{
	exit(2);
}

void
exith(void)
{
	unlink(multimon_pid_path);
	kill(0, SIGTERM);
}
