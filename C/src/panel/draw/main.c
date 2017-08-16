#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "errorwraps.h"
#include "../panel.h"

#define MAXLINE 1000
#define MAXBARVAR MAXLINE + 50
#define MAXITEM 10
#define MAXBOD 50

void setbarvar(char *, char *, char *);
char *get_workspace_icons(char *);

int main(int argc, char *argv[])
{
	char sys[MAXBARVAR] = "", batt[MAXBARVAR] = "", dbox[MAXBARVAR] = "", net[MAXBARVAR] = "",
		pia[MAXBARVAR] = "", updt[MAXBARVAR] = "", clean[MAXBARVAR] = "", vol[MAXBARVAR] = "",
		mail[MAXBARVAR] = "", surf[MAXBARVAR] = "", ham[MAXBARVAR] = "", alrm[MAXBARVAR] = "",
		wm[MAXBARVAR] = "";

	int i;
	bool last_item;
	char line[MAXLINE], *fmt, *pline, c, item[MAXITEM], *FG, *BG, BODY[MAXBOD];

	while (fgets(line, MAXLINE, stdin) != NULL) {
		*strchr(line, '\n') = '\0';
		switch (line[0]) {
			case 'S':
				snprintf(sys, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", GREY, line+1);
				/* setbarvar(sys, GREY, line); */
				break;
			case 'B':
				snprintf(batt, MAXBARVAR, "%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", line+1);
				/* setbarvar(batt, NULL, line); */
				break;
			case 'D':
				snprintf(dbox, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", BLUE, line+1);
				/* setbarvar(dbox, BLUE, line); */
				break;
			case 'X':
				snprintf(net, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", WHITE, line+1);
				/* setbarvar(net, WHITE, line); */
				break;
			case 'P':
				snprintf(pia, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", GREEN, line+1);
				/* setbarvar(pia, GREEN, line); */
				break;
			case 'U':
				snprintf(updt, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", RED, line+1);
				/* setbarvar(updt, RED, line); */
				break;
			case 'C':
				snprintf(clean, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", RED, line+1);
				/* setbarvar(clean, RED, line); */
				break;
			case 'V':
				snprintf(vol, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", WHITE, line+1);
				/* setbarvar(vol, WHITE, line); */
				break;
			case 'M':
				snprintf(mail, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", WHITE, line+1);
				/* setbarvar(mail, WHITE, line); */
				break;
			case 'Y':
				snprintf(surf, MAXBARVAR, "%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", line+1);
				/* setbarvar(surf, NULL, line); */
				break;
			case 'H':
				snprintf(ham, MAXBARVAR, "%%{F%s}%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", GREY, line+1);
				/* setbarvar(ham, GREY, line); */
				break;
			case 'A':
				snprintf(alrm, MAXBARVAR, "%%{B" COLOR_SYS_BG "}%s%%{B-}%%{F-}", line+1);
				/* setbarvar(alrm, NULL, line); */
				break;
			case 'W':
				pline = line + 1;
				last_item = false;
				memset(wm, 0, MAXBARVAR);
				while (!last_item) {
					i = 0;
					while ((c = *pline++) != ':') {
						if (c == '\0') {
							last_item = true;
							break;
						}
						item[i++] = c;
					}
					item[i] = '\0';

					switch (item[0]) {
						case 'M': case 'm':
							switch (item[0]) {
								case 'M':
									FG=COLOR_FOCUSED_MONITOR_FG;
									BG=COLOR_FOCUSED_MONITOR_BG;
									break;
								case 'm':
									FG=COLOR_MONITOR_FG;
									BG=COLOR_MONITOR_BG;
									break;
							}
							fmt = "%%{A:bspc monitor -f %s:} %s %%{A}";
							snprintf(BODY, MAXBOD, fmt, item+1, item+1);
							break;
						case 'f': case 'F': case 'o': case 'O': case 'u': case 'U':
							switch (item[0]) {
								case 'f':
									FG=COLOR_FREE_FG;
									BG=COLOR_FREE_BG;
									break;
								case 'F':
									FG=COLOR_FOCUSED_FREE_FG;
									BG=COLOR_FOCUSED_FREE_BG;
									break;
								case 'o':
									FG=COLOR_OCCUPIED_FG;
									BG=COLOR_OCCUPIED_BG;
									break;
								case 'O':
									FG=COLOR_FOCUSED_OCCUPIED_FG;
									BG=COLOR_FOCUSED_OCCUPIED_BG;
									break;
								case 'u':
									FG=COLOR_URGENT_FG;
									BG=COLOR_URGENT_BG;
									break;
								case 'U':
									FG=COLOR_FOCUSED_URGENT_FG;
									BG=COLOR_FOCUSED_URGENT_BG;
									break;
							}
							fmt = "%%{A:bspc desktop -f %s:} %s %%{A}";
							snprintf(BODY, MAXBOD, fmt, item+1, get_workspace_icons(item+1));
							break;
						default:
							continue;
					}

					snprintf(wm + strlen(wm), MAXBARVAR - strlen(wm), "%%{F%s}%%{B%s}%s%%{B-}%%{F-}", FG, BG, BODY);
				}

				break;
		}

		fmt = "%%{l}%s%%{c}%s%%{r}%%{T3}%s%s%s%s%s%s%s%s%%{S+}%%{l}  %s%%{c}%s%%{r}%s%%{T-}\n";
		fprintf(stdout, fmt, wm, sys, mail, batt, vol, pia, dbox, net, updt, clean, alrm, ham, surf);
		fflush(stdout);
	}

	exit(3);
}

void
setbarvar(char *barvar, char *FG, char *line)
{
	int length = sizeof(barvar);
	memset(barvar, 0, length);
	if (FG != NULL) {
		strcat(strcat(strcat(barvar, "%{F"), FG), "}");
	}
	strcat(barvar, "%{B" COLOR_SYS_BG "}");
	strcat(barvar, line+1);
	strcat(barvar, "%{B-}%{F-}");
}

char *
get_workspace_icons(char *name)
{
	if (((strcmp(name, "I") == 0) || (strcmp(name, "VI") == 0))) {
		return "\uf2d0";
	} else if ((strcmp(name, "II") == 0) || (strcmp(name, "VII") == 0)) {
		return "\uf268";
	} else if ((strcmp(name, "III") == 0) || (strcmp(name, "VIII") == 0)) {
		return "\uf1c1";
	} else if (strcmp(name, "IV") == 0) {
		return "A";
	} else if (strcmp(name, "V") == 0) {
		return "B";
	} else if (strcmp(name, "IX") == 0) {
		return "C";
	} else if (strcmp(name, "X") == 0) {
		return "D";
	}
}
