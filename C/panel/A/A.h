#ifndef A
#define A 0


// Libraries
#include <stdio.h>
#include <string.h>


// Definitions
#define MAX_CMD 200
#define BILLION 1000000000L
#define NEVER_DAY 3456000
#define HNSIZE 10

#define upd_pia 5
#define upd_batt 1
#define upd_net 8
#define upd_upd 86400
#define upd_dbox 5
#define upd_vol 1
#define upd_mail 15

extern int errno;


// Inline Function Definitions / Function Declarations
inline void err_ret(char *restrict alterr)
{
	fprintf(stderr, "%s\n", (errno != 0) ? strerror(errno) : alterr);
}


inline void write_fifo(char *restrict icon, int fd)
{
	write(fd, icon, strlen(icon));;
}

#endif /* ifndef A */
