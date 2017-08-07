dev: main.c
	gcc -g -Wall main.c

prod: main.c
	gcc -O2 -o ~/Dropbox/scripts/lemonbar/panel-poll main.c

test: a.out
	./a.out

clean:
	rm /tmp/panel-fifo

run: dev test
