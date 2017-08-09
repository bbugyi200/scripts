#ifndef SWITCH
#define SWITCH 0

#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define ALT_MAX 50

enum tstat { NONE, MAIN, ALT, BOTH };

typedef struct {
	enum tstat status;
	int desktop;
}target_data;


/* ----- Function Declarations ----- */
// Returns desktop # of focused desktop
int get_focused_desktop(void);

// Returns # of lines in 'wmctrl -l' that match given title
target_data get_target_data(const char *, const char *);

// Retrieves alt_{target/cmd} if ':' exists in {target/cmd}.
// Otherwise, alt_{target/cmd} = {target/cmd}
void getalt(char *, char *);


#endif /* ifndef SWITCH */
