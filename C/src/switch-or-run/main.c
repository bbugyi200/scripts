#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "switch.h"

int main(int argc, char *argv[])
{
	// Test Arguments
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

	// Assign arguments from argv
	char *target = argv[1];
	char alt_target[ALT_MAX], alt_cmd[ALT_MAX];
	strcpy(alt_target, target);
	char *cmd = argv[2];
	strcpy(alt_cmd, cmd);
	int desktop = argv[3][0] - '0';
	int alt_desktop = (desktop + 5) % 10;

	getalt(target, alt_target);
	getalt(cmd, alt_cmd);

	target_data tdata = get_target_data(target, alt_target);

	int focused_desktop = get_focused_desktop();

	char full_cmd[50], *next_cmd = cmd, *next_target = alt_target;
	int next_desktop = desktop;
	bool main_focused, alt_focused, target_focused;
	main_focused = (desktop == focused_desktop);
	alt_focused = (alt_desktop == focused_desktop);
	target_focused = (tdata.desktop == focused_desktop);

	// This assignment for next_desktop is valid for MAIN, ALT, and BOTH cases,
	// but not for case NONE.
	if (main_focused) {
		next_desktop = alt_desktop;
	} else {
		next_desktop = desktop;
	}

	const char *fmt = "bspc rule -a \"*:*\" -o desktop=^%d && %s &> /dev/null & bspc desktop -f ^%d";
	char *bspc_fmt = "bspc desktop -f ^%d";
	char bspc_cmd[strlen(bspc_fmt) + 1];
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
		default:
			sprintf(bspc_cmd, bspc_fmt, next_desktop);
			system(bspc_cmd);
			break;
	}

	return 0;
}
