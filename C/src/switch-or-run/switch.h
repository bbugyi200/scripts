#ifndef SWITCH
#define SWITCH 0

#include <stdio.h>


typedef struct {
	char *name;
	char *cmd;
	int desktop;
	int alt_desktop;
} WIN;


const char *fmt = "bspc rule -a \"*:*\" -o desktop=^%d && %s &> /dev/null & bspc desktop -f ^%d";


/* ----- Function Declarations ----- */
// Returns desktop # of focused desktop
int get_focused_desktop(void);

// Returns # of lines in 'wmctrl -l' that match given title
int count_titles(char *);

// Formats command string
static inline void get_full_cmd(char *cmd, char *full_cmd, int dt) {
	sprintf(full_cmd, fmt, dt, cmd, dt);
}


#endif /* ifndef SWITCH */
