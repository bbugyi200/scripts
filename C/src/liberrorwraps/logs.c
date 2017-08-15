#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <syslog.h>
#include <stdarg.h>
#include <stdbool.h>
#include "bugyi.h"

static void log_main(bool, int, const char *, va_list);

void
log_sys(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	log_main(true, errno, fmt, ap);
	va_end(ap);

	exit(1);
}

void
log_quit(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	log_main(false, 0, fmt, ap);
	va_end(ap);

	exit(1);
}

void
log_ret(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	log_main(false, 0, fmt, ap);
	va_end(ap);

	return;
}

static void
log_main(bool errnoflag, int error, const char *fmt, va_list ap)
{
	char buf[MAXLINE];

	vsnprintf(buf, MAXLINE-1, fmt, ap);
	if (errnoflag)
		snprintf(buf+strlen(buf), MAXLINE-strlen(buf)-1, ": %s", strerror(error));
	strcat(buf, "\n");
	syslog(LOG_ERR, "%s", buf);
}
