#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "draw.h"

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
				setbarvar(sys, GREY, line+1);
				break;
			case 'B':
				setbarvar(batt, "-", line+1);
				break;
			case 'D':
				setbarvar(dbox, "-", line+1);
				break;
			case 'X':
				setbarvar(net, WHITE, line+1);
				break;
			case 'P':
				setbarvar(pia, GREEN, line+1);
				break;
			case 'U':
				setbarvar(updt, RED, line+1);
				break;
			case 'C':
				setbarvar(clean, RED, line+1);
				break;
			case 'V':
				setbarvar(vol, WHITE, line+1);
				break;
			case 'M':
				setbarvar(mail, WHITE, line+1);
				break;
			case 'Y':
				setbarvar(surf, "-", line+1);
				break;
			case 'H':
				setbarvar(ham, GREY, line+1);
				break;
			case 'A':
				setbarvar(alrm, "-", line+1);
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

		fmt = "%%{l}%s%%{c}%s%%{r}%%{T3}%s%s%s%s%s%s%s%s%%{S+}%%{l}%s%%{c}%s%%{r}%s%%{T-}\n";
		fprintf(stdout, fmt,
				wm, // #1 Left
				sys, // #1 Center
				mail, batt, vol, pia, dbox, net, updt, clean, // #1 Right
				alrm, // #2 Left
				ham,  // #2 Center
				surf); // #2 Right

		fflush(stdout);
	}

	exit(3);
}

char *
get_workspace_icons(char *name)
{
	if (((strcmp(name, "I") == 0) || (strcmp(name, "VI") == 0)))
		return "\uf2d0";
	else if ((strcmp(name, "II") == 0) || (strcmp(name, "VII") == 0))
		return "\uf268";
	else if ((strcmp(name, "III") == 0) || (strcmp(name, "VIII") == 0))
		return "\uf1c1";
	else if (strcmp(name, "IV") == 0)
		return "A";
	else if (strcmp(name, "V") == 0)
		return "B";
	else if (strcmp(name, "IX") == 0)
		return "C";
	else if (strcmp(name, "X") == 0)
		return "D";
	else
		return NULL;
}
