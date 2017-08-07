#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
#include "poll.h"
#include "../panel.h"

#define BATT_ICON_MAX 30
#define SURF_ICON_MAX 50


int 	cnt_pia = upd_pia,		cnt_batt = upd_batt,	cnt_net = upd_net,
		cnt_upd = upd_upd,		cnt_dbox = upd_dbox,	cnt_mail = upd_mail,
		cnt_clean = upd_clean,	cnt_surf = upd_surf;

void err_ext(const char *);
void write_fifo(char *);

extern int fifo_fd;

int main(int argc, char *argv[])
{
	fifo_fd = open(fifo_path, O_RDWR);

	// Pipe Variables
	int pipefd[2];
	pid_t pid;
	FILE *pipe_output;
	char cmdout[MAX_CMD];


	// ----- Sets 'multi_mon' -----
	pipe(pipefd);
	if ((pid = fork()) < 0)
		perror(argv[0]);
	else if (pid == 0) {
		close(pipefd[0]);
		dup2(pipefd[1], STDOUT_FILENO);
		execl("/usr/bin/bspc", "bspc", "query", "--monitors", (char *)NULL);
	}

	close(pipefd[1]);
	waitpid(pid, NULL, 0);

	pipe_output = fdopen(pipefd[0], "r");

	errno = 0;
	int num_of_monitors;
	while (fgets(cmdout, MAX_CMD, pipe_output) != NULL) {
		num_of_monitors++;
	}
	if (errno)
		perror(argv[0]);
	fclose(pipe_output);

	bool multi_mon = (num_of_monitors > 1) ? true : false;

	// ----- Set constants based on hostname ------
	char hostname[HNSIZE], *net_dev;
	if (gethostname(hostname, HNSIZE) < 0)
		fprintf(stderr, "%s\n", "gethostname error");
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
	char *icon;

	// Battery
	int batt_nval;
	char *batt_color, *batt_icon, full_batt_icon[BATT_ICON_MAX], *bolt;

	// Surf
	int labels[3];
	char *colors[3];
	char full_surf_icon[SURF_ICON_MAX];
	

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

			if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
				err_ext("fgets");

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

			if (snprintf(full_batt_icon, BATT_ICON_MAX, "B%%{F%s}%s%s %d%%  \n", batt_color,
						bolt, batt_icon, batt_nval) < 0)
				fprintf(stderr, "battery: snprintf error");
			write_fifo(full_batt_icon);
			fclose(pipe_output);
			cnt_batt = 0;
		}

		// Dropbox
		if (cnt_dbox++ >= upd_dbox) {
			ecode = system("pgrep dropbox >& /dev/null");
			icon = (ecode == 0) ? "D" DBOX "  \n" : "D\n";
			write_fifo(icon);
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

			if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
				err_ext("fgets");


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
		if (cnt_mail++ >= upd_mail) {
			ecode = system("check_mail -q");
			icon = (ecode == 0) ? "M" MAIL "  \n" : "M\n";
			write_fifo(icon);
			cnt_mail = 0;
		}

		// Surf Check
		if (cnt_surf++ >= upd_surf && multi_mon) {
			ecode = system("~/Dropbox/scripts/python/SurfCheck.py");
			ecode = ecode / 256;  // 'system' returns multiple of 256
			labels[0] = ecode / 100; ecode = ecode - 100*labels[0];
			labels[1] = ecode / 10; ecode = ecode - 10*labels[1];
			labels[2] = ecode;

			for (int i = 0; i < 3; ++i) {
				switch (labels[i]) {
					case 0:
						colors[i] = RED;
						break;
					case 1:
						colors[i] = YELLOW;
						break;
					case 2:
						colors[i] = GREEN;
						break;
					default:
						colors[i] = WHITE;
				}
			}
			if (snprintf(full_surf_icon,
					SURF_ICON_MAX,
					"Y%%{F%s}" DIAMOND " %%{F%s}" DIAMOND " %%{F%s}" DIAMOND "  \n",
					colors[0], colors[1], colors[2]) < 0) 
				perror("snprintf");

			write_fifo(full_surf_icon);
			cnt_surf = 0;
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
