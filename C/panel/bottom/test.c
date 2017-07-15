#include "bpanel.h"

int main(int argc, char *argv[])
{
	char line[MAXLINE];
	int ofifo = open(fifo, O_WRONLY);
	int n;

	for(;;) {
		if ((n = read(0, line, MAXLINE)) == 0) {
			write(1, "n=0", 4);
			/* perror(argv[0]); */
		}
		line[n-1] = '\n';
		line[n] = '\0';
		write(ofifo, line, n);
	}
	return 0;
}
