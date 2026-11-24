# AppKit

The local profile exposes the documented NSColor sRGB constructor and
component properties, plus the common NSResponder, NSApplication, NSView,
and NSWindow class declarations and the window title property. It gets
NSObject through the Foundation layer's pinned Apple OSS objc4 headers.
The scalar ABI follows Apple's LP64 CGFloat documentation.

Clang InstallAPI emits the arm64 Objective-C class exports from the staged
headers. The installed AppKit image on macOS 26.5.2 (25F84) uses the
`Versions/C/AppKit` install name and reexports versioned Foundation. The recipe
passes the staged Foundation stub to InstallAPI to describe that edge and
provides both flat and versioned lookup paths. The Cocoa probe creates a color, checks all its components, and
checks the responder hierarchy without opening a window. Window creation,
event processing, and the remaining AppKit API require separate qualification.

```sh
dyld_info -dependents /System/Library/Frameworks/AppKit.framework/Versions/C/AppKit
```

- [NSColor class and components](https://developer.apple.com/documentation/appkit/nscolor?language=objc)
- [sRGB constructor](https://developer.apple.com/documentation/appkit/color-creation?language=objc)
- [CGFloat on 64-bit systems](https://developer.apple.com/documentation/corefoundation/cgfloat-swift.struct)
- [AppKit class catalog](https://developer.apple.com/documentation/appkit?language=objc)
