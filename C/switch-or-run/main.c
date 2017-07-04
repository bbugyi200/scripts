#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "switch.h"


int main(int argc, char *argv[])
{
    // Validate arguments
    if (argc < 4) {
        fprintf(stderr, "%s\n%s\n", "ERROR: Not enough arguments!",
                "switch-or-run {window} {cmd} {desktop}");
        return 1;
    }

    // Assign arguments from argv
    windowp->name = *++argv;
    char *cmd = *++argv;
    windowp->desktop = (*++argv)[0] - '0';
    windowp->alt_desktop = (windowp->desktop + 5) % 10;

    int num_open = count_titles(windowp->name);
    int focused_desktop = get_focused_desktop();

    char full_cmd[50];
    int dt, main_focused, alt_focused;

    // The following assignments make clear whether or not the primary or
    // alternate desktops are focused.
    //
    // If so, dt represents the desktop # of the next TARGET desktop
    main_focused = windowp->desktop == focused_desktop ? windowp->alt_desktop : 0;
    alt_focused = windowp->alt_desktop == focused_desktop ? windowp->desktop : 0;
    dt = main_focused ? main_focused : alt_focused;
    switch (num_open) {
        case 0:
            if (focused_desktop >= 6) {
                dt = windowp->alt_desktop;
            } else {
                dt = windowp->desktop;
            }

            get_full_cmd(cmd, full_cmd, dt);
            system(full_cmd);
            break;
        case 1:
            if (dt) {
                get_full_cmd(cmd, full_cmd, dt);
                system(full_cmd);
            }
            else {
                char wmctrl_cmd[20] = "wmctrl -a ";
                system(strcat(wmctrl_cmd, windowp->name));
            }
            break;
        case 2:
        default:
            dt = dt ? dt : windowp->desktop;
            char *bspc_fmt = "bspc desktop -f ^%d";
            char bspc_cmd[strlen(bspc_fmt)];
            sprintf(bspc_cmd, bspc_fmt, dt);
            system(bspc_cmd);
            break;
    }

    return 0;
}
