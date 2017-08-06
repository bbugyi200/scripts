#include <stdio.h>
#include <unistd.h>
#include "daemonize.h"

int main(int argc, char *argv[])
{
	daemonize(argv[0]);
	sleep(10);
	return 0;
}
