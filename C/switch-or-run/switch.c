#include <stdio.h>
#include <string.h>
#include <ctype.h>

int get_focused_desktop(void) {
	FILE *po = popen("wmctrl -d | grep \\*", "r");
	int desktop = fgetc(po) - '0';
	return desktop + 1;
}


int count_titles(char *title)
{
	FILE *po;
	if (strstr(title, ".") != NULL)
		po= popen("wmctrl -lx", "r");
	else
		po = popen("wmctrl -l", "r");
	char line[500], *linep;
	int count = 0;
	while (fgets(line, 500, po) != NULL) {
		if (strstr(line, title) != NULL)
			count++;
	}

	return count;
}
