#include <CoreFoundation/CoreFoundation.h>

CF_ENUM(UInt32) { kProbeCode = 42 };

CF_ASSUME_NONNULL_BEGIN
static CFErrorDomain error_domain(CFErrorRef error) {
    return CFErrorGetDomain(error);
}
CF_ASSUME_NONNULL_END

int main(void) {
    CFErrorDomain domain = CFStringCreateCopy(NULL, CFSTR("Framework linkage"));
    if (!domain)
        return 1;
    CFErrorRef error = CFErrorCreate(NULL, domain, kProbeCode, NULL);
    if (!error) {
        CFRelease(domain);
        return 1;
    }
    CFTypeRef retained = CFRetain(error);
    int failed = retained != error || !CFEqual(error_domain(error), domain);
    CFRelease(retained);
    CFRelease(error);
    CFRelease(domain);
    return failed;
}
