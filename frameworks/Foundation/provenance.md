# Foundation

The trial exposes selected Objective-C string, collection, data, error, URL,
number, and date APIs. It uses `NSObject.h` and `objc.h` from the pinned Apple
OSS objc4 installation and `CFBase.h` from the CoreFoundation recipe.

The remaining declarations are local renderings of public declarations and
ABI facts. Apple documents the LP64 integer widths, both `NSRange` fields,
and the Objective-C collection methods. The runtime probe checks range
layout and by-value returns as well as behavior for the supported classes.
Other Foundation features require additional declarations and probes.

- [Apple OSS objc4](https://github.com/apple-oss-distributions/objc4)
- [LP64 Foundation scalar types](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/64bitPorting/HighLevelAPIs/HighLevelAPIs.html)
- [Range fields](https://developer.apple.com/documentation/xcode/reading-an-exception-message)
- [Range construction](https://developer.apple.com/documentation/foundation/nsmakerange(_:_:)?language=objc)
- [Object and collection declarations](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/FoundationTypesandCollections/FoundationTypesandCollections.html)
- [Foundation DocC catalog](https://developer.apple.com/documentation/foundation?language=objc)

Preserve the qualified SDK Gen 0.0.4 Foundation stub's exports. On macOS
26.5.2 (25F84), the installed Foundation dylib reexports CoreFoundation on
arm64 and x86_64. CoreFoundation owns Clang's
Objective-C constant string symbol. The staged patch adds that reexport to
the pinned SDK Gen input. The CoreFoundation recipe provides the versioned
path the linker resolves. Xcode 26.5 is a validation reference.

```sh
dyld_info -dependents /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation
```
