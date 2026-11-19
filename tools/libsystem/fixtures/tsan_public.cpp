#if defined(CHECK_CONTEXT)
#include <ucontext.h>

static ucontext_t caller;
static ucontext_t other;
alignas(16) static char stack[65536];
static volatile int resumed;

static void enter_other()
{
    resumed = 1;
    if (setcontext(&caller) == -1)
        resumed = -1;
}

int check_context()
{
    if (getcontext(&other) == -1)
        return 1;
    other.uc_stack.ss_sp = stack;
    other.uc_stack.ss_size = sizeof(stack);
    other.uc_link = &caller;
    makecontext(&other, enter_other, 0);
    return swapcontext(&caller, &other) != 0 || resumed != 1;
}

#elif defined(CHECK_REALPATH)
#include <limits.h>
#include <stdlib.h>

int check_realpath()
{
    char resolved[PATH_MAX];
    return realpath("/", resolved) != resolved || resolved[0] != '/' || resolved[1] != '\0';
}

#elif defined(CHECK_FILENO)
#include <stdio.h>

int macro_fileno(FILE *stream)
{
    return fileno_unlocked(stream);
}

#undef fileno_unlocked
#include "compiler_rt_stdio.h"

int call_fileno(void *stream)
{
    return fileno_unlocked(stream);
}

#elif defined(CHECK_EXECUTABLE)
#include <stdio.h>

int check_context();
int check_realpath();
int macro_fileno(FILE *);
int call_fileno(void *);

int main()
{
    if (check_context() != 0 || check_realpath() != 0)
        return 1;
    FILE *file = fopen("/dev/null", "r");
    if (!file)
        return 2;
    int fd = call_fileno(file);
    int expect = macro_fileno(file);
    return fclose(file) != 0 || fd < 0 || fd != expect;
}
#endif
