switch-or-run "tabbed" "tabbed" "5"
until wmctrl -lx | grep "tabbed.tabbed"; do
    sleep 0.5
done
wmctrl -r :ACTIVE:
zathura -e `wmctrl -lx | grep "tabbed.tabbed" | cut -d' ' -f1` "$1"
