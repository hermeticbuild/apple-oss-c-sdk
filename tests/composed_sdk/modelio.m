#import <ModelIO/ModelIO.h>

_Static_assert(__builtin_types_compatible_p(
    __typeof__(((MDLMesh *)0).submeshes.firstObject), MDLSubmesh *),
    "MDLMesh submeshes preserve their element type through NSArray");

int main(void) {
    @autoreleasepool {
        return [MDLAsset class] == Nil;
    }
}
