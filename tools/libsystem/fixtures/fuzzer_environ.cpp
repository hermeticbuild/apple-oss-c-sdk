#include <spawn.h>
#include <stdlib.h>
#include <sys/wait.h>

extern "C" char **environ;

int main()
{
    if (setenv("LIBSYSTEM_FUZZER_ENVIRON_TEST", "visible", 1) != 0)
        return 1;

    char shell[] = "sh";
    char option[] = "-c";
    char command[] = "test \"$LIBSYSTEM_FUZZER_ENVIRON_TEST\" = visible";
    char *args[] = {shell, option, command, nullptr};
    pid_t child;
    if (posix_spawn(&child, "/bin/sh", nullptr, nullptr, args, environ) != 0)
        return 2;

    int status;
    return waitpid(child, &status, 0) != child || !WIFEXITED(status) || WEXITSTATUS(status) != 0;
}
