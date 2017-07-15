#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#define upd_pia 5
#define upd_batt 1
#define upd_net 8
#define upd_upd 86400
#define upd_dbox 5
#define upd_vol 1
#define upd_mail 15

#define MAX_CMD 200
#define BILLION 1000000000L
#define NEVER_DAY 3456000
#define HNSIZE 10

int 	cnt_pia = upd_pia,	cnt_batt = upd_batt,	cnt_net = upd_net,
    	cnt_upd = upd_upd,	cnt_dbox = upd_dbox,	cnt_vol = upd_vol,
    	cnt_mail = upd_mail;

int fifo_fd;

void err_ret(char *);
void write_fifo(char *);

int main(void)
{
	errno = 0;

	// Filter counters and set constants based on hostname
	char hostname[HNSIZE];
	gethostname(hostname, HNSIZE);
	char *net_dev;
	if (strncmp(hostname, "athena", 6) == 0) {
		cnt_batt = NEVER_DAY;
		net_dev = "enp2s0";
	} else {
		cnt_pia = NEVER_DAY;
		net_dev = "wlo1";
	}

	const char *fifo_path = getenv("PANEL_FIFO");

	struct stat sb;

	if (stat(fifo_path, &sb) != 0 || !S_ISFIFO(sb.st_mode)) {
		fifo_fd = mkfifo(fifo_path, 0666);
	} else {
		fifo_fd = open(fifo_path, O_RDWR);
	}

	int ecode;
	char *icon;
	FILE *po;
	char cmdout[MAX_CMD];

	for(;;) {
        struct timespec start, end;
        clock_gettime(CLOCK_MONOTONIC, &start);

		// OS Update Checker
		if (cnt_upd++ >= upd_upd) {
			ecode = system("python ~/Dropbox/scripts/python/UpdtCheck.py");
			icon = (ecode == 0) ? "U" : "U\uf0aa  ";
			write_fifo(icon);
			cnt_upd = 0;
		}

		// New Mail
		if (cnt_mail++ >= upd_mail) {
			ecode = system("check_mail -q");
			icon = (ecode == 0) ? "M" : "M\uf003  ";
			write_fifo(icon);
			cnt_mail = 0;
		}

		// Volume
		if (cnt_vol++ >= upd_vol) {
			if ((po = popen("amixer get Master | sed -n 's/^.*\\[\\([0-9]\\+\\)%.*$/\\1/p' | uniq", "r")) == NULL)
				err_ret("popen error: volume");
			if (fgets(cmdout, 3, po) == NULL)
				err_ret("fgets error: volume");
			int volume = atoi(cmdout);

			if (volume == 0) {
				icon = "V\uf026  ";
			} else {
				icon = (volume >= 50) ? "V\uf028  " : "V\uf027  ";
			}
			write_fifo(icon);
			cnt_vol = 0;
		}

		// Dropbox
		if (cnt_dbox++ >= upd_dbox) {
			ecode = system("pgrep dropbox >& /dev/null");
			icon = (ecode == 0) ? "D\uf16b  " : "D";
			write_fifo(icon);
			cnt_dbox = 0;
		}

		// PIA
		if (cnt_pia++ >= upd_pia) {
			ecode = system("pgrep openvpn >& /dev/null");
			icon = (ecode == 0) ? "P\uf17b  " : "P";
			write_fifo(icon);
			cnt_pia = 0;
		}

		// Network Connection
		char pcmd[20] = "ip link show "; 
		if (cnt_net++ >= upd_net) {
			if ((po = popen(strcat(pcmd, net_dev), "r")) == NULL)
				err_ret("popen error: network");
			if (fgets(cmdout, MAX_CMD, po) == NULL)
				err_ret("fgets error: network");

			if (strstr(cmdout, "state UP") == NULL) {
				icon = "X\uf119  ";
			} else {
				ecode = system("ping -q -w 1 -c 1 google.com >& /dev/null");
				icon = (ecode == 0) ? "X\uf118  " : "X\uf11a  ";
			}

			write_fifo(icon);
			cnt_net = 0;
		}

        clock_gettime(CLOCK_MONOTONIC, &end);
        u_int64_t diff = BILLION * (end.tv_sec - start.tv_sec) + end.tv_nsec - start.tv_nsec;

		struct timespec sleep_time;
		sleep_time.tv_sec = 0;
		sleep_time.tv_nsec = (diff < BILLION) ? BILLION - diff : 0;

		nanosleep(&sleep_time, NULL);
	}

    return 0;
}


inline void err_ret(char *restrict alterr)
{
	fprintf(stderr, "%s\n", (errno != 0) ? strerror(errno) : alterr);
	exit(1);
}


inline void write_fifo(char *restrict icon)
{
	int length = strlen(icon) + 1;
	char Icon[length];
	strcpy(Icon, icon);
	strcat(Icon, "\n");
	write(fifo_fd, Icon, length);;
}
