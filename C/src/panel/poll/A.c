#include <unistd.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "A.h"

void set_fifo()
{
	const char *fifo_path = getenv("PANEL_FIFO");
	struct stat sb;
	if (stat(fifo_path, &sb) != 0 || !S_ISFIFO(sb.st_mode)) {
		fifo_fd = mkfifo(fifo_path, 0666);
	} else {
		fifo_fd = open(fifo_path, O_RDWR);
	}
}
