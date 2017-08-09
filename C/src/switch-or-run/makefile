dev:
	gcc -g -Wall main.c switch.c

prod:
	gcc -O2 -o ~/Dropbox/scripts/config/switch-or-run main.c switch.c

atest:
	./a.out "okular.okular" "okular" "3"

stest:
	sleep 3 && ./a.out "okular.okular" "okular" "3"

ctest:
	sleep 3 && ./a.out "okular.okular:zathura.Zathura" "okular:zathura" "3"
	

run: dev test
