dev: main.c
	gcc -g -Wall main.c

prod: main.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/panel-poll main.c

vol-dev: volume.c
	gcc -g -Wall volume.c

vol-prod: volume.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/volume-panel-update volume.c

test: a.out
	./a.out

clean:
	rm /tmp/panel-fifo

run: dev test
