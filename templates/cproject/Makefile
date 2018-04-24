CC=gcc
CFLAGS=-Wall -Werror -g -std=c99
LDLIBS=
name=PROGRAM_NAME
bin=bin
objects=main.c

.PHONY: all addr clean

all: $(bin)/$(name)

addr: CFLAGS+= -fsanitize=address
addr: all

$(bin)/%: $(objects) | $(bin)
	$(CC) $(CFLAGS) $^ $(LDLIBS) -o $@

$(bin):
	mkdir -p $(bin)

clean:
	rm -rf **/*.o bin $(bin)/runtests $(bin)/$(name)
