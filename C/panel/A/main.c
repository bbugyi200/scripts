#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
#include "A.h"
#include "../panel.h"

int 	cnt_pia = upd_pia,	cnt_batt = upd_batt,	cnt_net = upd_net,
		cnt_upd = upd_upd,	cnt_dbox = upd_dbox,	cnt_vol = upd_vol,
		cnt_mail = upd_mail;

void err_ret(char *, int);
void write_fifo(char *, int);

int main(void)
{
	errno = 0;

	// Set constants based on hostname
	char hostname[HNSIZE], *net_dev;
	gethostname(hostname, HNSIZE);
	bool is_laptop = false;
	if (strncmp(hostname, "athena", 6) == 0) {
		net_dev = "enp2s0";
	} else {
		net_dev = "wlo1";
		is_laptop = true;
	}

	// Get FIFO Descriptor
	const char *fifo_path = getenv("PANEL_FIFO");
	struct stat sb;
	int fifo_fd;
	if (stat(fifo_path, &sb) != 0 || !S_ISFIFO(sb.st_mode)) {
		fifo_fd = mkfifo(fifo_path, 0666);
	} else {
		fifo_fd = open(fifo_path, O_RDWR);
	}

	// Loop Variable Declarations
	int ecode, batt_nval, volume;
	u_int64_t diff;
	struct timespec start, end, sleep_time;
	char *icon, cmdout[MAX_CMD], *batt_color,
		 *batt_icon, full_batt_icon[30], *bolt;

	pid_t pid = 0;
	int pipefd[4];
	FILE *pipe_output;
	int status;

	// Main Loop
	for(;;) {
		clock_gettime(CLOCK_MONOTONIC, &start);

		// OS Update Checker
		if (cnt_upd++ >= upd_upd) {
			ecode = system("python ~/Dropbox/scripts/python/UpdtCheck.py");
			icon = (ecode == 0) ? "U\n" : "U\uf0aa  \n";
			write_fifo(icon, fifo_fd);
			cnt_upd = 0;
		}

		// New Mail
		if (cnt_mail++ >= upd_mail) {
			ecode = system("check_mail -q");
			icon = (ecode == 0) ? "M\n" : "M\uf003  \n";
			write_fifo(icon, fifo_fd);
			cnt_mail = 0;
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
			pipe_output = fdopen(pipefd[0], "r");

			waitpid(pid, &status, 0);

			if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
				err_ret("fgets error: battery power-check", errno);

			if (strstr(cmdout, "Discharging") == NULL)
				bolt = "\uf0e7 ";
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
				batt_icon = "\uf240";
			} else if (batt_nval >= 35) {
				batt_color = YELLOW;
				batt_icon = "\uf242";
			} else {
				batt_color = RED;
				batt_icon = "\uf243";
			}

			sprintf(full_batt_icon, "B%%{F%s}%s%s %d%%  \n", batt_color,
					bolt, batt_icon, batt_nval);
			write_fifo(full_batt_icon, fifo_fd);
			fclose(pipe_output);
			cnt_batt = 0;
		}

		// Volume
		if (cnt_vol++ >= upd_vol) {
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

			if (volume == 0) {
				icon = "V\uf026  \n";
			} else {
				icon = (volume >= 50) ? "V\uf028  \n" : "V\uf027  \n";
			}

			write_fifo(icon, fifo_fd);
			fclose(pipe_output);
			cnt_vol = 0;
		}

		// Dropbox
		if (cnt_dbox++ >= upd_dbox) {
			ecode = system("pgrep dropbox >& /dev/null");
			icon = (ecode == 0) ? "D\uf16b  \n" : "D\n";
			write_fifo(icon, fifo_fd);
			cnt_dbox = 0;
		}

		// PIA
		if (cnt_pia++ >= upd_pia) {
			ecode = system("pgrep openvpn >& /dev/null");
			icon = (ecode == 0) ? "P\uf17b  \n" : "P\n";
			write_fifo(icon, fifo_fd);
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
			pipe_output = fdopen(pipefd[0], "r");

			if (fgets(cmdout, MAX_CMD, pipe_output) == NULL)
				err_ret("fgets error: network", errno);

			waitpid(pid, &status, 0);

			if (strstr(cmdout, "state UP") == NULL) {
				icon = "X\uf119  \n";
			} else {
				ecode = system("ping -q -w 1 -c 1 google.com >& /dev/null");
				icon = (ecode == 0) ? "X\uf118  \n" : "X\uf11a  \n";
			}

			write_fifo(icon, fifo_fd);
			fclose(pipe_output);
			cnt_net = 0;
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
