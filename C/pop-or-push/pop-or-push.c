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

    char *window, desktop[1];
    window = *++argv;

    FILE *fp;
    char top[20], cmd[30], *fmt;
    const char *filename = "/tmp/pop_window.txt";

    if (fp = fopen(filename, "r")) {
        fmt = "wmctrl -r %s -t %s";
        fscanf(fp, "%s", desktop);
        remove(filename);
    }
    else {
        fmt = "wmctrl -R %s && bspc node -f last; test %s";

        char cmd2[40];
        const char *fmt2 = "wmctrl -l | grep -i %s | tr -s ' ' | cut -d ' ' -f2";
        sprintf(cmd2, fmt2, window);
        FILE *po = popen(cmd2, "r");
        fscanf(po, "%s", desktop);

        fp = fopen(filename, "w");
        fprintf(fp, "%s", desktop);
    }

    sprintf(cmd, fmt, window, desktop);
    fclose(fp);
    system(cmd);
    return 0;
}
