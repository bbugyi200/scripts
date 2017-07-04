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
    FILE *po = popen("wmctrl -l", "r");
    char line[200], *linep;
    int count = 0;
    while (fgets(line, 200, po) != NULL) {
        linep = line;
        while ((*linep++ = tolower(*linep)))
            ;
        if (strstr(line, title) != NULL)
            count++;
    }

    return count;
}
