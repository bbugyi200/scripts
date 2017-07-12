#include "bpanel.h"

int main(int argc, char *argv[])
{
	mkfifo(fifo, 0777);

	int ofifo = open(fifo, O_RDWR);
	char line[MAXLINE] = "%{c}";
	int n;

	while((n = read(ofifo, line+4, MAXLINE)) > 0) {
		write(1, line, n+4);
		sleep(1);
	}

	close(ofifo);
	return 0;
}
