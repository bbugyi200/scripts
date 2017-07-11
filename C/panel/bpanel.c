#include <stdio.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>

#define MAXLINE 200

const char *fifo = "/tmp/bpanel_fifo";

int main(int argc, char *argv[])
{
	/* mkfifo(fifo, 0666); */

	int ofifo = open(fifo, O_RDWR);
	char line[MAXLINE];
	int n;

	while((n = read(ofifo, line, MAXLINE)) > 0) {
		line[n-1] = '\0';
		printf("%%{c}%s\n", line);
		fflush(stdout);
		sleep(1);
	}

	close(ofifo);
	return 0;
}
