#ifndef PANEL
#define PANEL 0

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/syslog.h>

#define MAX_CMD 300

// Colors
#define GREEN "#0BF816"
#define YELLOW "#EBEE27"
#define RED "#FB0611"
#define BLUE "#3C4BF7"
#define WHITE "#FFFFFF"
#define GREY "#D9D9D9"

#define COLOR_DEFAULT_FG "#a7a5a5"
#define COLOR_DEFAULT_BG "#333232"
#define COLOR_MONITOR_FG "#8dbcdf"
#define COLOR_MONITOR_BG "#333232"
#define COLOR_FOCUSED_MONITOR_FG "#b1d0e8"
#define COLOR_FOCUSED_MONITOR_BG "#144b6c"
#define COLOR_FREE_FG "#737171"
#define COLOR_FREE_BG "#333232"
#define COLOR_FOCUSED_FREE_FG "#000000"
#define COLOR_FOCUSED_FREE_BG "#504e4e"
#define COLOR_OCCUPIED_FG "#a7a5a5"
#define COLOR_OCCUPIED_BG "#333232"
#define COLOR_FOCUSED_OCCUPIED_FG "#d6d3d2"
#define COLOR_FOCUSED_OCCUPIED_BG "#504e4e"
#define COLOR_URGENT_FG "#f15d66"
#define COLOR_URGENT_BG "#333232"
#define COLOR_FOCUSED_URGENT_FG "#501d1f"
#define COLOR_FOCUSED_URGENT_BG "#d5443e"
#define COLOR_STATE_FG "#89b09c"
#define COLOR_STATE_BG "#333232"
#define COLOR_TITLE_FG "#a8a2c0"
#define COLOR_TITLE_BG "#333232"
#define COLOR_SYS_FG "#b1a57d"
#define COLOR_SYS_BG "#333232"

int fifo_fd;
const char *fifo_path = "/tmp/panel-fifo";

inline void write_fifo(char *restrict icon)
{
	write(fifo_fd, icon, strlen(icon));;
}

#endif /* ifndef PANEL */
