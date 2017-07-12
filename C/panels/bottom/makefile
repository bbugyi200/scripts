dev: main.c
	gcc $?

dry:
	./a.out

damp:
	./a.out > foo.txt

wet:
	./a.out | lemonbar -b -a 32 -n "${PANEL_WM_NAME}" -g x${PANEL_HEIGHT} -f "Inconsolata-12:Bold" -f "Font Awesome-12" -f "Font Awesome-12" -F "#D9D9D9" -B "#333232" | sh

%: %.c
	gcc -o $* $*.c
