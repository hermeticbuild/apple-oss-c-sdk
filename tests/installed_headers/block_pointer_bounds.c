#include <ptrcheck.h>
#include <Block.h>

#if !__has_feature(bounds_safety)
#error This fixture requires bounds safety
#endif

void *__single copy_one(const void *__single block) {
    return _Block_copy(block);
}

void release_one(const void *__unsafe_indexable block) {
#if defined(TEST_UNSAFE_RAW_RELEASE)
    _Block_release(block);
#else
    Block_release(block);
#endif
}
