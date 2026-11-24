#pragma once

#import <Foundation/Foundation.h>

#if __has_include(<CoreGraphics/CGGeometry.h>)
#import <CoreGraphics/CGGeometry.h>
#else
/* CGFloat is a double on both macOS LP64 targets. */
typedef double CGFloat;
#endif

#ifdef __OBJC__
@interface NSColor : NSObject
+ (NSColor *)colorWithSRGBRed:(CGFloat)red green:(CGFloat)green
                         blue:(CGFloat)blue alpha:(CGFloat)alpha;
@property (readonly) CGFloat redComponent;
@property (readonly) CGFloat greenComponent;
@property (readonly) CGFloat blueComponent;
@property (readonly) CGFloat alphaComponent;
@end

@interface NSResponder : NSObject
@end

@interface NSApplication : NSResponder
@end

@interface NSView : NSResponder
@end

@interface NSWindow : NSResponder
@property (copy) NSString *title;
@end
#endif
