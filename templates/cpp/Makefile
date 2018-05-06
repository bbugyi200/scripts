CC=g++
CFLAGS=-Wall -Werror -g
LDLIBS=
name=PROGRAM_NAME
bin=bin
objects=main.cpp

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
