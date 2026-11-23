#pragma once

#include <CoreFoundation/CFBase.h>
#include <objc/objc.h>

/* The trial targets macOS LP64. The ranges follow Apple's documented
 * NSUInteger location/length contract and are validated by value. */
typedef long NSInteger;
typedef unsigned long NSUInteger;
typedef double NSTimeInterval;
typedef struct _NSRange {
    NSUInteger location;
    NSUInteger length;
} NSRange;

static inline NSRange NSMakeRange(NSUInteger location, NSUInteger length) {
    NSRange result = {location, length};
    return result;
}

static inline NSUInteger NSMaxRange(NSRange range) {
    return range.location + range.length;
}

#ifdef __OBJC__
#import <objc/NSObject.h>

@class NSString;
@protocol NSCopying;
typedef NSString *NSErrorDomain;

@interface NSString : NSObject
+ (instancetype)stringWithUTF8String:(const char *)bytes;
+ (instancetype)stringWithString:(NSString *)string;
- (NSString *)stringByAppendingString:(NSString *)string;
- (NSRange)rangeOfString:(NSString *)string;
- (BOOL)isEqualToString:(NSString *)string;
@property (readonly) const char *UTF8String;
@property (readonly) NSUInteger length;
@end

@interface NSArray<__covariant ObjectType> : NSObject
+ (instancetype)array;
+ (instancetype)arrayWithObject:(ObjectType)object;
+ (instancetype)arrayWithObjects:(const ObjectType [])objects count:(NSUInteger)count;
- (ObjectType)objectAtIndex:(NSUInteger)index;
@property (readonly) NSUInteger count;
@property (readonly) ObjectType firstObject;
@property (readonly) ObjectType lastObject;
@end

@interface NSDictionary<__covariant KeyType, __covariant ObjectType> : NSObject
+ (instancetype)dictionaryWithObjects:(const ObjectType [])objects
                               forKeys:(const id<NSCopying> [])keys
                                 count:(NSUInteger)count;
@property (readonly) NSUInteger count;
@end

@interface NSData : NSObject
+ (instancetype)dataWithBytes:(const void *)bytes length:(NSUInteger)length;
@property (readonly) const void *bytes;
@property (readonly) NSUInteger length;
@end

@interface NSError : NSObject
+ (instancetype)errorWithDomain:(NSErrorDomain)domain code:(NSInteger)code
                       userInfo:(NSDictionary<NSString *, id> *)details;
@property (readonly) NSErrorDomain domain;
@property (readonly) NSInteger code;
@property (readonly) NSString *localizedDescription;
@property (readonly) NSDictionary<NSString *, id> *userInfo;
@end

@interface NSURL : NSObject
+ (instancetype)URLWithString:(NSString *)string;
@property (readonly) NSString *absoluteString;
@property (readonly) NSString *path;
@property (readonly, getter=isFileURL) BOOL fileURL;
@end

@interface NSValue : NSObject
@end

@interface NSNumber : NSValue
+ (NSNumber *)numberWithInt:(int)value;
+ (NSNumber *)numberWithDouble:(double)value;
@property (readonly) double doubleValue;
@property (readonly) NSInteger integerValue;
@end

@interface NSDate : NSObject
+ (instancetype)dateWithTimeIntervalSince1970:(NSTimeInterval)interval;
@property (readonly) NSTimeInterval timeIntervalSince1970;
@end
#endif
