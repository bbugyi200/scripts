dev: main.c A.c
	gcc -g -Wall main.c A.c

prod: main.c A.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/panel_a main.c A.c

vol-dev: volume.c A.c
	gcc -g -Wall volume.c A.c

vol-prod: volume.c A.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/volume-panel-update volume.c A.c

test: a.out
	./a.out

clean:
	rm /tmp/panel-fifo

run: dev test
