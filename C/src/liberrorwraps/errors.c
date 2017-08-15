#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdarg.h>
#include <stdbool.h>
#include "bugyi.h"

static void err_main(bool, int, const char *, va_list);

void
err_sys(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	err_main(true, errno, fmt, ap);
	va_end(ap);

	exit(1);
}

void
err_quit(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	err_main(false, 0, fmt, ap);
	va_end(ap);

	exit(1);
}

void
err_ret(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	err_main(false, 0, fmt, ap);
	va_end(ap);

	return;
}

static void
err_main(bool errnoflag, int error, const char *fmt, va_list ap)
{
	char buf[MAXLINE];

	vsnprintf(buf, MAXLINE-1, fmt, ap);

	if (errnoflag)
		snprintf(buf+strlen(buf), MAXLINE-strlen(buf)-1, ": %s", strerror(error));
	strcat(buf, "\n");

	fflush(stdout);
	fputs(buf, stderr);
	fflush(NULL);
}
