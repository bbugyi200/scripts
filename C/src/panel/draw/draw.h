#ifndef DRAW
#define DRAW

#include "../panel.h"

#define MAXLINE 1000
#define MAXBARVAR MAXLINE + 50
#define MAXITEM 50
#define MAXBOD 50

inline void
setbarvar(char *barvar, char *color, char *item)
{
	snprintf(barvar, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", color, item);
}

#endif /* ifndef DRAW */
