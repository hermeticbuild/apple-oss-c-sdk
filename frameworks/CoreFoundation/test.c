#include <CoreFoundation/CoreFoundation.h>

int main(void) {
    CFStringRef copy = CFStringCreateCopy(NULL, CFSTR("Framework linkage"));
    if (!copy)
        return 1;
    CFRelease(copy);
    return 0;
}
