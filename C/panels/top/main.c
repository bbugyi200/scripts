#include <stdio.h>
#include <stdlib.h>

#define upd_pia 5
#define upd_batt 1
#define upd_net 8
#define upd_upd 86400
#define upd_dbox 5
#define upd_vol 1
#define upd_mail 15

int cnt_pia=upd_pia,
    cnt_batt=upd_batt,
    cnt_net=upd_net,
    cnt_upd=upd_upd,
    cnt_dbox=upd_dbox,
    cnt_vol=upd_vol,
    cnt_mail=upd_mail;

int main(int argc, char *argv[])
{
    const char* FIFO = getenv("PANEL_FIFO");
    for(;;){
        // Dropbox
        if (cnt_dbox++ >= upd_dbox) {
            if (system("pgrep dropbox") != 0) {
                // write to FIFO
            } else {
                // write to FIFO
            }
        }

        // OS Update
        if (cnt_upd++ >= upd_upd) {
            if (system("python ~/Dropbox/scripts/python/UpdtCheck.py") != 0) {

            } else {

            }
        }
    }
    return 0;
}
