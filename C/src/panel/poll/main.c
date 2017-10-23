#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
#include <ctype.h>
#include "errorwraps.h"
#include "bugyi.h"
#include "poll.h"
#include "../panel.h"

#define MAX_ICON 50


int 	cnt_pia = upd_pia,		cnt_batt = upd_batt,	cnt_net = upd_net,
		cnt_upd = upd_upd,		cnt_dbox = upd_dbox,	cnt_mail = upd_mail,
		cnt_clean = upd_clean,	cnt_surf = upd_surf,	cnt_ham = upd_ham,
		cnt_temp = upd_temp;

extern int fifo_fd;

int main(int argc, char *argv[])
{
	fifo_fd = open(fifo_path, O_RDWR);

	// Pipe Variables
	int pipefd[4], status;
	pid_t pid;
	FILE *pipe_output;
	char cmdout[MAXLINE];

	// ----- Set constants based on hostname ------
	char hostname[HNSIZE], *net_dev;
	if (gethostname(hostname, HNSIZE) < 0)
		log_sys("gethostname");

	bool is_laptop = false;
	if (strncmp(hostname, "athena", 6) == 0) {
		net_dev = "enp2s0";
	} else {
		net_dev = "wlo1";
		is_laptop = true;
	}


	// ----- Loop Variable Declarations -----
	// General
	int ecode;
	u_int64_t diff;
	struct timespec start, end, sleep_time;
	char *icon, full_icon[MAX_ICON];

	// Battery
	int batt_nval;
	char *batt_color, *batt_icon, *bolt;

	// Surf
	char *colors[3], label;

	// Dropbox
	int fd_dbox = open(dbox_ipath, OFLAGS, OMODE);
	if (fd_dbox < 0)
		log_sys("open");
	

	// ----- Main Loop -----
	for(;;) {
		clock_gettime(CLOCK_MONOTONIC, &start);

		// OS Update Checker
		if (cnt_upd++ >= upd_upd) {
			ecode = system("~/Dropbox/scripts/python/MaintChck.py --update");
			icon = (ecode == 0) ? "U\n" : "U" UPDT "  \n";
			write_fifo(icon);
			cnt_upd = 0;
		}

		// Filesystem Cleanup Check
		if (cnt_clean++ >= upd_clean) {
			ecode = system("~/Dropbox/scripts/python/MaintChck.py --cleanup");
			icon = (ecode == 0) ? "C\n" : "C" TRASH "  \n";
			write_fifo(icon);
			cnt_clean = 0;
		}

		// Battery
		if (cnt_batt++ >= upd_batt && is_laptop) {
			pipe(pipefd);
			pid = fork();
			if (pid == 0) {
				close(pipefd[0]);
				dup2(pipefd[1], STDOUT_FILENO);
				execl("/usr/bin/acpi", "acpi", "--battery", (char *) NULL);
			}

			close(pipefd[1]);
			waitpid(pid, NULL, 0);

			pipe_output = fdopen(pipefd[0], "r");

			if (fgets(cmdout, MAXLINE, pipe_output) == NULL)
				log_sys("fgets");

			if (strstr(cmdout, "Discharging") == NULL)
				bolt = BOLT " ";
			else
				bolt = "";

			// Find Comma
			char *batt_val = cmdout;
			while (*batt_val++ != ',')
				;
			char *batt_valp = batt_val++;
			while (*(++batt_valp) != '%')
				;
			*batt_valp = '\0';

			batt_nval = (int) strtol(batt_val, NULL, 0);

			if (batt_nval >= 70) {
				batt_color = GREEN;
				batt_icon = HBATT;
			} else if (batt_nval >= 35) {
				batt_color = YELLOW;
				batt_icon = MBATT;
			} else {
				batt_color = RED;
				batt_icon = LBATT;
			}

			if (snprintf(full_icon, MAX_ICON, "B%%{F%s}%s%s %d%%  \n", batt_color,
						bolt, batt_icon, batt_nval) < 0)
				fprintf(stderr, "battery: snprintf error");
			write_fifo(full_icon);
			fclose(pipe_output);
			cnt_batt = 0;
		}

		// Dropbox
		if (cnt_dbox++ >= upd_dbox) {
			if (lockf(fd_dbox, F_TLOCK, 0) < 0)
				log_ret("%s is already locked.", dbox_ipath);
			else {
				ecode = system("pgrep dropbox >& /dev/null");
				icon = (ecode == 0) ? "D%{F" BLUE "}" DBOX "  \n" : "D\n";
				write_fifo(icon);
				if (lockf(fd_dbox, F_ULOCK, 0) < 0)
					log_sys("Unable to unlock %s.", dbox_ipath);
			}

			cnt_dbox = 0;
		}

		// PIA
		if (cnt_pia++ >= upd_pia) {
			ecode = system("pgrep openvpn >& /dev/null");
			icon = (ecode == 0) ? "P" PIA "  \n" : "P\n";
			write_fifo(icon);
			cnt_pia = 0;
		}

		// Network Connection
		if (cnt_net++ >= upd_net) {
			pipe(pipefd);
			pid = fork();
			if (pid == 0) {
				close(pipefd[0]);
				dup2(pipefd[1], STDOUT_FILENO);
				execl("/usr/bin/ip", "ip", "link", "show", net_dev, (char *) NULL);
			}

			close(pipefd[1]);
			waitpid(pid, NULL, 0);

			pipe_output = fdopen(pipefd[0], "r");

			if (fgets(cmdout, MAXLINE, pipe_output) == NULL)
				log_sys("fgets");


			if (strstr(cmdout, "state UP") == NULL) {
				icon = "X" FROWN "  \n";
			} else {
				ecode = system("ping -q -w 1 -c 1 google.com >& /dev/null");
				icon = (ecode == 0) ? "X" SMILE "  \n" : "X" MEH "  \n";
			}

			write_fifo(icon);
			fclose(pipe_output);
			cnt_net = 0;
		}

		// New Mail
		/* if (cnt_mail++ >= upd_mail) { */
		/* 	ecode = system("check_mail -q"); */
		/* 	icon = (ecode == 0) ? "M" MAIL "  \n" : "M\n"; */
		/* 	write_fifo(icon); */
		/* 	cnt_mail = 0; */
		/* } */

		// Hamster
		if (cnt_ham++ >= upd_ham) {
			if ((status = system("/home/bryan/Dropbox/scripts/python/panel-hamster.py")) != 0)
				log_ret("system(\"%s\") = %d", "/home/bryan/Dropbox/scripts/python/panel-hamster.py", status/256);
			cnt_ham = 0;
		}

		// Temperature
		if (cnt_temp++ >= upd_temp) {
			pipe(pipefd);
			if ((pid = fork()) < 0)
				log_sys("fork");
			else if (pid == 0) {
				close(pipefd[0]);
				dup2(pipefd[1], STDOUT_FILENO);
				execl("/usr/bin/weather-report", "weather-report", "-q", "--headers", "Temperature", "--no-cache", "08901", (char *) NULL);
			}

			close(pipefd[1]);
			waitpid(pid, &status, 0);
			if (status != 0)
				log_msg("weather-report failed with 'status = %d'", status);

			pipe(pipefd + 2);
			if ((pid = fork()) < 0)
				log_sys("fork");
			else if (pid == 0) {
				close(pipefd[2]);
				dup2(pipefd[0], STDIN_FILENO);
				dup2(pipefd[3], STDOUT_FILENO);
				execl("/usr/bin/gawk", "gawk", "{printf \"%.0f\u00b0F\", $2}", (char *) NULL);
			}

			close(pipefd[3]);
			waitpid(pid, &status, 0);
			if (status != 0)
				log_msg("gawk failed with 'status = %d'", status);

			pipe_output = fdopen(pipefd[2], "r");

			if (fgets(cmdout, MAX_CMD, pipe_output) < 0)
				log_sys("fgets");

			if (snprintf(full_icon, MAX_ICON, "T %s  \n", cmdout) < 0)
				log_sys("snprintf (temp)");

			write_fifo(full_icon);
			cnt_temp = 0;
		}

		// sleep_time =  (1 second) - (loop iteration time)
		clock_gettime(CLOCK_MONOTONIC, &end);
		diff = BILLION * (end.tv_sec - start.tv_sec) + end.tv_nsec - start.tv_nsec;
		sleep_time.tv_sec = 0;
		sleep_time.tv_nsec = (diff < BILLION) ? BILLION - diff : 0;

		nanosleep(&sleep_time, NULL);
	}

	return 0;
}
