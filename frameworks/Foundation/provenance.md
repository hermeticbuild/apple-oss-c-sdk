# Foundation

The trial exposes selected Objective-C string, collection, data, error, URL,
number, and date APIs. It uses `NSObject.h` and `objc.h` from the pinned Apple
OSS objc4 installation and `CFBase.h` from the CoreFoundation recipe.

The remaining declarations are local renderings of public declarations and
ABI facts. Apple documents the LP64 integer widths, both `NSRange` fields,
and the Objective-C collection methods. The runtime probe checks range
layout and by-value returns as well as behavior for the supported classes.
Other Foundation features require additional declarations and probes.

The Foundation enum, option, and nullability macros delegate to the
corresponding definitions in the staged Apple OSS CoreFoundation headers.
The composed SDK probe uses an `NS_ENUM` type and a declaration inside a
nonnull region on arm64.
[Apple OSS enum macros](https://github.com/apple-oss-distributions/CF/blob/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3/CFAvailability.h#L195-L215)

- [Apple OSS objc4](https://github.com/apple-oss-distributions/objc4)
- [LP64 Foundation scalar types](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/64bitPorting/HighLevelAPIs/HighLevelAPIs.html)
- [Range fields](https://developer.apple.com/documentation/xcode/reading-an-exception-message)
- [Range construction](https://developer.apple.com/documentation/foundation/nsmakerange(_:_:)?language=objc)
- [Object and collection declarations](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/FoundationTypesandCollections/FoundationTypesandCollections.html)
- [Foundation DocC catalog](https://developer.apple.com/documentation/foundation?language=objc)

Preserve the qualified SDK Gen 0.0.4 Foundation stub's exports. The macOS
26.5.2 (25F84) Foundation dylib has the `Versions/C/Foundation` install
name and reexports CoreFoundation. CoreFoundation owns Clang's
Objective-C constant string symbol. The staged patch adds that reexport to
the pinned SDK Gen input. The Foundation and CoreFoundation recipes provide
the versioned paths the linker resolves. Xcode 26.5 is a validation reference.

```sh
dyld_info -dependents /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation
```

The local voice Foundation layer includes `VoiceFoundation.h` from its
umbrella. Apply [voice-modulemap.patch](voice-modulemap.patch) to that
prepared bundle before composition. The textual entry follows the existing
`NSPathUtilities.h` entry. It gives the voice declarations access to types
defined in the umbrella. The C++20 `test-Foundation-modules` target
reproduces the missing `NSUInteger` diagnostic without the patch and
compiles, links and runs with it.

```sh
patch -s -f -F 0 -V none -p1 -d "$VOICE_FOUNDATION_FRAMEWORK" \
  < frameworks/Foundation/voice-modulemap.patch
patch -s -f -F 0 -V none -p1 -d "$VOICE_FOUNDATION_FRAMEWORK" \
  < frameworks/Foundation/voice-array-generics.patch
```

The second patch gives the voice layer's mutable array an invariant
element parameter and passes that parameter to its `NSArray` superclass.
The composed `test-modelio` probe checks the type of
`mesh.submeshes.firstObject` through both classes.
[Apple's MDLMesh property declaration](https://developer.apple.com/documentation/modelio/mdlmesh/submeshes?language=objc)
