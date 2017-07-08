#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
	if (argc < 2) {
		printf("%s\n%s\n",
			   "ERROR: Not enough arguments!",
			   "SYNTAX: pop-or-push <win>");
		return 1;
	}

	char *window, desktop;
	window = *++argv;

	FILE *fp;
	char top[20], cmd[30], *fmt;
	const char *filename = "/tmp/pop_window.txt";

	if (fp = fopen(filename, "r")) {
		fmt = "wmctrl -r %s -t %c";
		fscanf(fp, "%c", &desktop);
		remove(filename);
	}
	else {
		fmt = "wmctrl -R %s && test %c";

		char cmd2[40];
		const char *fmt2 = "wmctrl -l | grep -i %s | tr -s ' ' | cut -d ' ' -f2";
		sprintf(cmd2, fmt2, window);
		FILE *po = popen(cmd2, "r");
		fscanf(po, "%s", &desktop);

		fp = fopen(filename, "w");
		fprintf(fp, "%s", &desktop);
	}

	printf("desktop = %c\n", desktop);
	printf("fmt = %s\n", fmt);
	sprintf(cmd, fmt, window, desktop);
	fclose(fp);
	printf("cmd = %s\n", cmd);
	system(cmd);
	return 0;
}
