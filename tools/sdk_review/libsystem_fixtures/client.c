#include <stdio.h>
#include <unistd.h>

int main(void) {
    return getpid() > 0 && puts("libSystem client passed") >= 0 ? 0 : 1;
}
