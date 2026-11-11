#import <Foundation/Foundation.h>
#import <IOKit/IOKitLib.h>

@interface AuthBypass : NSObject
+ (void)fuzzAppleAPFSVolumeBSDClient:(void (^)(NSString *))log;
@end

@implementation AuthBypass

+ (void)fuzzAppleAPFSVolumeBSDClient:(void (^)(NSString *))log {
    log(@"  [*] Searching for AppleAPFSVolumeBSDClient...");
    
    io_service_t service = IOServiceGetMatchingService(0, IOServiceMatching("AppleAPFSVolumeBSDClient"));
    if (!service) {
        log(@"  [-] Not found, trying AppleAPFSVolume...");
        service = IOServiceGetMatchingService(0, IOServiceMatching("AppleAPFSVolume"));
    }
    
    if (!service) {
        log(@"  [-] No APFS services found");
        return;
    }
    
    log(@"  [+] Found APFS service");
    
    for (uint32_t connType = 0; connType < 3; connType++) {
        io_connect_t conn;
        kern_return_t kr = IOServiceOpen(service, mach_task_self(), connType, &conn);
        
        if (kr != KERN_SUCCESS) {
            log([NSString stringWithFormat:@"  [-] Open type %u failed: 0x%x", connType, kr]);
            continue;
        }
        
        log([NSString stringWithFormat:@"  [+] OPENED type %u, fuzzing selectors...", connType]);
        
        for (int selector = 0; selector < 200; selector++) {
            uint64_t input[16] = {0};
            uint64_t output[16] = {0};
            uint32_t outputCnt = 16;
            
            input[0] = 0;
            input[1] = 1;
            input[2] = getpid();
            input[3] = 0;
            
            kr = IOConnectCallMethod(conn, selector, input, 16, NULL, 0, output, &outputCnt, NULL, NULL);
            
            if (kr == KERN_SUCCESS) {
                log([NSString stringWithFormat:@"  🎯 SELECTOR %d SUCCESS (type %u)!", selector, connType]);
            }
            
            usleep(1000);
        }
        
        IOServiceClose(conn);
    }
    
    IOObjectRelease(service);
    log(@"  [*] Auth bypass fuzz complete");
}

@end
