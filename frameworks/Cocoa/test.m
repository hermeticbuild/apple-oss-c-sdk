#import <Cocoa/Cocoa.h>
#import <AppKit/NSColor.h>
#import <CoreData/NSEntityDescription.h>

int main(void) {
    @autoreleasepool {
        NSColor *color = [NSColor colorWithSRGBRed:0.25 green:0.5 blue:0.75 alpha:1];
        NSString *description = color.description;
        NSManagedObjectModel *model = [[NSManagedObjectModel alloc] init];
        NSEntityDescription *entity = [NSEntityDescription new];
        entity.name = @"TrialEntity";
        model.entities = [NSArray arrayWithObject:entity];

        return color.redComponent != 0.25 || color.greenComponent != 0.5 ||
               color.blueComponent != 0.75 || color.alphaComponent != 1 ||
               description.length == 0 || model.entities.count != 1 ||
               ![model.entities.firstObject.name isEqualToString:@"TrialEntity"] ||
               ![NSWindow isSubclassOfClass:[NSResponder class]] ||
               ![NSView isSubclassOfClass:[NSResponder class]] ||
               ![NSApplication isSubclassOfClass:[NSResponder class]];
    }
}
