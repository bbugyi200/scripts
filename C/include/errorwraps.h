#ifndef ERRORWRAPS
#define ERRORWRAPS

void err_sys(const char *, ...);
void err_quit(const char*, ...);
void err_ret(const char*, ...);

void log_sys(const char *, ...);
void log_quit(const char*, ...);
void log_ret(const char *, ...);

#endif /* ifndef ERRORWRAPS */
