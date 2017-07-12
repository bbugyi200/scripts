#ifndef BPANEL
#define BPANEL 0

#define MAXLINE 200
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>

const char *fifo = "/tmp/bpanel_fifo";

#endif /* ifndef BPANEL */
