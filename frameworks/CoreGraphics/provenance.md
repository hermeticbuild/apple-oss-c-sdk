# CoreGraphics geometry

The local recipe moves the generated 26.5 `CGFloat` and `CGPoint`
declarations into the public `CGGeometry.h` path. The umbrella uses the
same declarations. The module map treats the geometry header as textual
so the local AppKit event declaration can include it without compiling
the entire CoreGraphics umbrella as Objective-C++.

[Apple's geometry API](https://developer.apple.com/documentation/coregraphics/cggeometry)
· [Clang textual headers](https://clang.llvm.org/docs/Modules.html#header-declaration)

The fixture checks the layout and both include orders for arm64.
The Cocoa module fixture checks the local framework composition.
