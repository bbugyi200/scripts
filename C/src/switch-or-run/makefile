dev:
	gcc -g -Wall main.c switch.c

prod:
	gcc -O2 -o ~/Dropbox/scripts/config/switch-or-run main.c switch.c

test:
	./a.out "Termite" "termite -e 'tm-init Terminal'" "1"

run: dev test
