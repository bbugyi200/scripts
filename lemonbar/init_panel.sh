#! /bin/bash

cd /

if xdo id -a "$PANEL_WM_NAME" > /dev/null ; then
    printf "%s\n" "The panel is already running." >&2
    exit 1
fi

trap 'trap - TERM; kill 0' INT TERM QUIT EXIT

[ -e "$PANEL_FIFO" ] && rm "$PANEL_FIFO"
mkfifo "$PANEL_FIFO"

. panel_config


bspc config top_padding $PANEL_HEIGHT
bspc subscribe report > "$PANEL_FIFO" &
clock -sf 'S%A, %B %d %Y   %I:%M%p' > "$PANEL_FIFO" &

FONT_SIZE="10"
if [[ $(hostname) == "athena" ]]; then
	FONT_SIZE="12"
fi

num_of_monitors=$(bspc query --monitors | wc -l)
~/Dropbox/scripts/lemonbar/panel_a $num_of_monitors &

panel_bar < "$PANEL_FIFO" | lemonbar -a 32 -n "$PANEL_WM_NAME" -g x$PANEL_HEIGHT -f "Inconsolata-$FONT_SIZE:Bold" -f "Font Awesome-$FONT_SIZE" -f "Font Awesome-14" -F "$COLOR_DEFAULT_FG" -B "$COLOR_DEFAULT_BG" | sh &

wait
