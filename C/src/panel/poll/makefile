dev: main.c
	gcc -g -Wall main.c -lerrorwraps

dev-opt:
	gcc -O2 -g -Wall main.c -lerrorwraps

prod: main.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/panel-poll main.c -lerrorwraps

test: a.out
	./a.out

clean:
	rm /tmp/panel-fifo

run: dev test
