#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

int main(int argc, char *argv[])
{
	// Handle Program Arguments
	if (argc < 2) {
		printf("%s\n%s\n",
			   "ERROR: Not enough arguments!",
			   "SYNTAX: window-stack <win>");
		return 1;
	}
	char *window, desktop;
	window = argv[1];


	// Create 'tmpdir' if it doesn't exist already
	char tmpdir[30] = "/tmp/window-stack";
	struct stat sb;
	if (stat(tmpdir, &sb) != 0 || !S_ISDIR(sb.st_mode)) {
		mkdir(tmpdir, 0777);
	}


	// Build 'filepath' from 'tmpdir' and 'window'
	char filebase[20];
	sprintf(filebase, "/%s.txt", window);
	char *filepath = strcat(tmpdir, filebase);


	// If filepath exists...
	FILE *fp;
	char cmd[30], *fmt;
	if (fp = fopen(filepath, "r")) {
		fmt = "wmctrl -r %s -t %c";
		fscanf(fp, "%c", &desktop);
		remove(filepath);
	}
	else {
		fmt = "wmctrl -R %s && test %c";

		char get_desktop_cmd[40];
		const char *fmt2 = "wmctrl -l | grep -i %s | tr -s ' ' | cut -d ' ' -f2";
		sprintf(get_desktop_cmd, fmt2, window);
		FILE *po = popen(get_desktop_cmd, "r");
		fscanf(po, "%s", &desktop);
		fp = fopen(filepath, "w");
		fprintf(fp, "%s", &desktop);
	}

	sprintf(cmd, fmt, window, desktop);
	fclose(fp);
	system(cmd);
	return 0;
}
