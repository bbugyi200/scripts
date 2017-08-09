#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "switch.h"

int main(int argc, char *argv[])
{
	// ----- Test Arguments -----
	
	/* char **argv = malloc(4 * sizeof(char *)); */
	/* for (int i = 0; i < 4; ++i) { */
	/* 	argv[i] = malloc(255 * sizeof(char)); */
	/* } */

	/* strcpy(argv[1], "okular.okular:zathura.Zathura"); */
	/* strcpy(argv[2], "okular:zathura"); */
	/* strcpy(argv[3], "3"); */

	/* strcpy(argv[1], "google-chrome.Google-chrome"); */
	/* strcpy(argv[2], "google-chrome-stable"); */
	/* strcpy(argv[3], "2"); */

	// ----- argv assignments -----
	char *target = argv[1];
	char alt_target[ALT_MAX], alt_cmd[ALT_MAX];
	char *cmd = argv[2];
	int desktop = argv[3][0] - '0';
	int alt_desktop = (desktop + 5) % 10;

	strcpy(alt_target, target);
	strcpy(alt_cmd, cmd);
	getalt(target, alt_target);
	getalt(cmd, alt_cmd);

	// ----- Data Assignments needed for Switch logic -----
	target_data tdata = get_target_data(target, alt_target);

	const char *fmt = "bspc rule -a \"*:*\" -o desktop=^%d && %s &> /dev/null & bspc desktop -f ^%d";
	const char *bspc_fmt = "bspc desktop -f ^%d";

	// next_target and next_cmd are preset for ALT
	char full_cmd[50],
		 *next_cmd = cmd,
		 *next_target = alt_target,
		 bspc_cmd[strlen(bspc_fmt) + 1];

	int focused_desktop = get_focused_desktop();

	bool main_focused = (desktop == focused_desktop),
		 alt_focused = (alt_desktop == focused_desktop),
		 target_focused = (tdata.desktop == focused_desktop);

	// This assignment for next_desktop is valid for MAIN, ALT, and BOTH cases,
	// but not for case NONE.
	int next_desktop;
	if (main_focused) {
		next_desktop = alt_desktop;
	} else {
		next_desktop = desktop;
	}

	// ----- Switch Logic -----
	switch (tdata.status) {
		case NONE:
			if (focused_desktop >= 6) {
				next_desktop = alt_desktop;
			} else {
				next_desktop = desktop;
			}

			sprintf(full_cmd, fmt, next_desktop, cmd, next_desktop);
			system(full_cmd);
			break;
		case MAIN:
			next_cmd = alt_cmd;
			next_target = target;
		case ALT:
			if (target_focused) {
				sprintf(full_cmd, fmt, next_desktop, next_cmd, next_desktop);
				system(full_cmd);
			}
			else {
				char wmctrl_cmd[100] = "wmctrl -xa ";
				system(strcat(wmctrl_cmd, next_target));
			}
			break;
		case BOTH:
			sprintf(bspc_cmd, bspc_fmt, next_desktop);
			system(bspc_cmd);
			break;
	}

	return 0;
}
