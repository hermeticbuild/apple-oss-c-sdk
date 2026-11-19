#include <errno.h>
#include <unistd.h>

extern int close_nocancel(int fd) __asm__("_close$NOCANCEL");

int main(void) {
    int fds[2];
    if (pipe(fds) != 0)
        return 1;
    if (close_nocancel(fds[0]) != 0)
        return 2;
    if (close_nocancel(fds[0]) != -1 || errno != EBADF)
        return 3;
    return close(fds[1]) != 0;
}
