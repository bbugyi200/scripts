#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <wait.h>
#include <sys/stat.h>
#include "daemonize.h"
#include "../panel.h"

#define OFLAGS O_RDWR | O_CREAT
#define OMODE S_IRUSR | S_IWUSR

void exith(void);
void sighan(int);
void set_fifo(int *);
void err_ext(const char *);

const char *flpath = "/home/bryan/.panel.pid";

int
main(int argc, char *argv[])
{
	// ----- Check pid File -----
	int fd = open(flpath, OFLAGS, OMODE);

	if (fd < 0)
		err_ext("open");

	if (lockf(fd, F_TLOCK, 0) < 0) {
		fprintf(stderr, "%s\n", "The panel is already running!");
		_exit(1);
	}

	// ----- Daemonize this Process -----
	daemonize(argv[0]);

	// ----- Initialize Handlers -----
	atexit(exith);

	struct sigaction sa;
	sigset_t mask;
	sigemptyset(&mask);

	sa.sa_handler = sighan;
	sa.sa_mask = mask;

	if (sigaction(SIGTERM, &sa, NULL) < 0)
		err_ext("sigaction");
	if (sigaction(SIGINT, &sa, NULL) < 0)
		err_ext("sigaction");
	if (sigaction(SIGQUIT, &sa, NULL) < 0)
		err_ext("sigaction");

	// ----- Lock pid File -----
	fd = open(flpath, OFLAGS, OMODE);

	if (fd < 0)
		err_ext("open");

	if (lockf(fd, F_TLOCK, 0) < 0) {
		syslog(LOG_ERR, "%s\n", "The panel is already running!");
		_exit(1);
	}

	dprintf(fd, "%d", getpid());

	// ----- Fork Child Processes -----
	pid_t pid;
	int fifo_fd, pipefd[2];
	set_fifo(&fifo_fd);

	char hostname[10];
	int font_size;
	if (gethostname(hostname, 10) < 0)
		err_ext("gethostname");
	font_size = (strncmp(hostname, "athena", 6) == 0) ? 12 : 10;
	

	if (system("bspc config top_padding 24") != 0)
		fprintf(stderr, "%s\n", "'bspc config' failed");


	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		dup2(fifo_fd, STDOUT_FILENO);
		execl("/usr/bin/bspc", "bspc", "subscribe", "report", (char *)NULL);
	}

	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		dup2(fifo_fd, STDOUT_FILENO);
		execl("/usr/bin/clock", "clock", "-sf", "S%A, %B %d %Y   %I:%M%p", (char *)NULL);
	}


	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		execl("/usr/local/bin/panel-poll", "panel-poll", (char *)NULL);
	}

	// Volume Initialization
	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		execl("/usr/local/bin/volume-panel-update", "volume-panel-update", (char *) NULL);
	}

	waitpid(pid, NULL, 0);


	pipe(pipefd);
	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		close(pipefd[0]);
		dup2(fifo_fd, STDIN_FILENO);
		dup2(pipefd[1], STDOUT_FILENO);
		execl("/bin/sh", "sh", "/usr/local/bin/panel_bar", (char *)NULL);
	}

	char inconsolata[30], font_awesome[20];
	if (sprintf(inconsolata, "Inconsolata-%d:Bold", font_size) < 0)
		err_ext("sprintf");
	if (sprintf(font_awesome, "Font Awesome-%d", font_size) < 0)
		err_ext("sprintf");

	if ((pid = fork()) < 0)
		err_ext("fork");
	else if (pid == 0) {
		dup2(pipefd[0], STDIN_FILENO);
		execl("/usr/bin/lemonbar", "lemonbar", "-a32", "-gx24", "-f", inconsolata, "-f", font_awesome, "-f", "Font Awesome-14", "-F" COLOR_DEFAULT_FG, "-B" COLOR_DEFAULT_BG, (char *)NULL);
	}

	close(pipefd[1]);
	waitpid(pid, NULL, 0);
	exit(3);
}

void
sighan(int signo)
{
	exit(2);
}

void
exith(void)
{
	unlink(flpath);
	printf("\n\n%s\n", "Goodbye Cruel World!");
	kill(0, SIGTERM);
}

void
set_fifo(int *fd)
{
	struct stat sb;
	if (stat(fifo_path, &sb) != 0 || !S_ISFIFO(sb.st_mode)) {
		if (mkfifo(fifo_path, 0666) < 0)
			err_ext("mkfifo");
		*fd = open(fifo_path, O_RDWR);
	} else {
		*fd = open(fifo_path, O_RDWR);
	}
}
