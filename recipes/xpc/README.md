# XPC object type

The Security code-signing header declares `SecCodeCreateWithXPCMessage`
with an `xpc_object_t` parameter. Install that type using the fallback in
Apple's BSD-licensed WebKit from the macOS 26.5 source distribution. Keep
libdispatch's object declaration in Objective-C and the void-pointer type
in C. Xcode 26.5 confirms the type in both modes for arm64 and x86_64.
This header covers the object type. The XPC client API remains open.

[Pinned WebKit fallback](https://github.com/apple-oss-distributions/WebKit/blob/2a36545bf8dd89a417b724184900270fb2f523aa/Source/WTF/wtf/spi/darwin/XPCSPI.h)
· [Published type](https://developer.apple.com/documentation/xpc/xpc_object_t?language=objc)
