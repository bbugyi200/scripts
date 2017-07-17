#ifndef A
#define A 0


// ----- Libraries ------
#include <stdio.h>
#include <string.h>


// ----- Definitions -----
#define MAX_CMD 200
#define BILLION 1000000000L
#define NEVER_DAY 3456000
#define HNSIZE 10

// Update Timers
#define upd_pia 5
#define upd_batt 1
#define upd_net 8
#define upd_upd 86400
#define upd_dbox 5
#define upd_vol 1
#define upd_mail 15

// Unicode Font Awesome Icons
#define UPDT "\uf0aa"
#define MAIL "\uf003"
#define BOLT "\uf0e7"
#define HBATT "\uf240"
#define MBATT "\uf242"
#define LBATT "\uf243"
#define EDOT "\u25e6"
#define DOT "\u2022"
#define STAR "\u2605"
#define DBOX "\uf16b"
#define PIA "\uf17b"
#define FROWN "\uf119"
#define SMILE "\uf118"
#define MEH "\uf11a"

int fifo_fd;

// ----- Inline Function Definitions / Function Declarations ------
inline void err_ret(char *restrict alterr, int err)
{
	fprintf(stderr, "%s\n", (err != 0) ? strerror(err) : alterr);
}


inline void write_fifo(char *restrict icon)
{
	write(fifo_fd, icon, strlen(icon));;
}

#endif /* ifndef A */
