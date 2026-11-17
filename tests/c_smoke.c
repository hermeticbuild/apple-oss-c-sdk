#include <CoreFoundation/CoreFoundation.h>
#include <mach/mach.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>

int c_smoke(void) {
    pthread_t thread = pthread_self();
    CFStringRef string = CFSTR("header probe");
    CFRelease(string);
    return (thread != NULL) + (int)sizeof(struct sockaddr) + (int)sizeof(mach_port_t);
}
