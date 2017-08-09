#include <ctype.h>
#include "switch.h"

int
get_focused_desktop(void)
{
	FILE *po = popen("wmctrl -d | grep \\*", "r");
	int desktop = fgetc(po) - '0';
	return desktop + 1;
}

target_data
get_target_data(const char *target, const char *alt_target)
{
	FILE *po;
	target_data tdata;
	tdata.status = NONE;
	tdata.desktop = -1;

	if (strstr(target, ".") || strstr(alt_target, "."))
		po= popen("wmctrl -lx", "r");
	else
		po = popen("wmctrl -l", "r");
	char line[500];
	while (fgets(line, 500, po) != NULL) {
		if (strstr(line, target)) {
			if(tdata.status)
				tdata.status = BOTH;
			else
				tdata.status = MAIN;
		} else if (strstr(line, alt_target)) {
			if (tdata.status)
				tdata.status = BOTH;
			else
				tdata.status = ALT;
		} else {
			continue;
		}

		int found = 0;
		char *linep = line;
		while (found < 2 && linep++) {
			if (found) {
				if (isdigit(*linep)) {
					tdata.desktop = (*linep) - '0';
					tdata.desktop++;
					found++;
				}
			} else {
				if (isspace(*linep)) {
					found++;
				}
			}
		}
	}

	return tdata;
}

void
getalt(char *full, char *alt)
{
	while ((*(++full) != ':'))
	{
		if(!(*full))
			return;
	}

	*full++ = '\0';

	while ((*alt++ = *full++))
		;
}
