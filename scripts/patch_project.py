#!/usr/bin/env python3
"""F1OOB build fix.

Creates the IOConnectTrap runtime shim, wires it into the target's Sources
phase, and adds the frameworks the linker needs.
"""

import pathlib
import re

PROJ = pathlib.Path("F1OOB.xcodeproj/project.pbxproj")
SRC = pathlib.Path("Sources")
ROOT = pathlib.Path(".")

BUILD_FILE = "A1B2C3D4A1B2C3D4A1B2C3D4"
FILE_REF = "A1B2C3D4A1B2C3D4A1B2C3D5"

HEADER = """//
//  IOKitTrapShim.h
//
//  IOConnectTrap0-6 are declared in IOKitLib.h but are not exported by the
//  iOS IOKit stub, so linking against them fails. Resolve at runtime instead.
//
//  IOKit headers are private and often absent from the iPhoneOS SDK, so the
//  types are supplied from mach/mach.h when IOKitLib.h cannot be found.
//

#if __has_include(<IOKit/IOKitLib.h>)
#import <IOKit/IOKitLib.h>
#else
#import <mach/mach.h>
typedef mach_port_t io_connect_t;
#endif

kern_return_t shim_IOConnectTrap0(io_connect_t connect, uint32_t index, uint64_t a);
kern_return_t shim_IOConnectTrap1(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b);
kern_return_t shim_IOConnectTrap2(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b, uint64_t c);
kern_return_t shim_IOConnectTrap3(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b, uint64_t c, uint64_t d);
kern_return_t shim_IOConnectTrap4(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e);
kern_return_t shim_IOConnectTrap5(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e, uint64_t f);
kern_return_t shim_IOConnectTrap6(io_connect_t connect, uint32_t index, uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e, uint64_t f, uint64_t g);

#ifndef F1OOB_KEEP_RAW_TRAPS
#define IOConnectTrap0 shim_IOConnectTrap0
#define IOConnectTrap1 shim_IOConnectTrap1
#define IOConnectTrap2 shim_IOConnectTrap2
#define IOConnectTrap3 shim_IOConnectTrap3
#define IOConnectTrap4 shim_IOConnectTrap4
#define IOConnectTrap5 shim_IOConnectTrap5
#define IOConnectTrap6 shim_IOConnectTrap6
#endif
"""

IMPL = """//
//  IOKitTrapShim.m
//

#import "IOKitTrapShim.h"
#import <dlfcn.h>

#define F1OOB_TRAP(N, TYPES, ARGS)                                          \\
    static kern_return_t (*f1oob_real_##N) TYPES;                           \\
    kern_return_t shim_IOConnectTrap##N TYPES {                             \\
        if (!f1oob_real_##N)                                                \\
            f1oob_real_##N = (kern_return_t (*) TYPES)                      \\
                dlsym(RTLD_DEFAULT, "IOConnectTrap" #N);                    \\
        if (!f1oob_real_##N)                                                \\
            return KERN_FAILURE;                                            \\
        return f1oob_real_##N ARGS;                                         \\
    }

F1OOB_TRAP(0, (io_connect_t c, uint32_t i, uint64_t a), (c, i, a))
F1OOB_TRAP(1, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b), (c, i, a, b))
F1OOB_TRAP(2, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b, uint64_t d), (c, i, a, b, d))
F1OOB_TRAP(3, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b, uint64_t d, uint64_t e), (c, i, a, b, d, e))
F1OOB_TRAP(4, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b, uint64_t d, uint64_t e, uint64_t f), (c, i, a, b, d, e, f))
F1OOB_TRAP(5, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b, uint64_t d, uint64_t e, uint64_t f, uint64_t g), (c, i, a, b, d, e, f, g))
F1OOB_TRAP(6, (io_connect_t c, uint32_t i, uint64_t a, uint64_t b, uint64_t d, uint64_t e, uint64_t f, uint64_t g, uint64_t h), (c, i, a, b, d, e, f, g, h))
"""

LDFLAGS = (
    '\t\t\t\tOTHER_LDFLAGS = ("-framework", "UIKit", "-framework", '
    '"Foundation", "-framework", "IOKit", '
    '"-Wl,-undefined,dynamic_lookup");\n'
)


def write_sources():
    """Write to both root and Sources so group resolution cannot miss."""
    SRC.mkdir(parents=True, exist_ok=True)
    for base in (ROOT, SRC):
        (base / "IOKitTrapShim.h").write_text(HEADER)
        (base / "IOKitTrapShim.m").write_text(IMPL)
    print("shim written to root and Sources/")


def target_blocks(text):
    offsets = []
    pos = 0
    while True:
        i = text.find("buildSettings = {\n", pos)
        if i == -1:
            return offsets
        end = text.find("\n\t\t\t};", i)
        body = text[i:end if end != -1 else len(text)]
        if "PRODUCT_BUNDLE_IDENTIFIER" in body:
            offsets.append(i + len("buildSettings = {\n"))
        pos = i + 1


def set_ldflags(text):
    text = re.sub(r"[ \t]*OTHER_LDFLAGS = \([^)]*\);\n", "", text)
    offsets = target_blocks(text)
    if not offsets:
        offsets = [m.end() for m in re.finditer(r"buildSettings = \{\n", text)]
    for off in sorted(offsets, reverse=True):
        text = text[:off] + LDFLAGS + text[off:]
    print(f"OTHER_LDFLAGS written to {len(offsets)} block(s)")
    return text


def wire(text):
    if "PBXFileSystemSynchronizedRootGroup" in text:
        print("synchronized folder layout, no per-file wiring needed")
        return text
    if FILE_REF in text:
        print("already wired")
        return text

    text = text.replace(
        "/* Begin PBXBuildFile section */\n",
        "/* Begin PBXBuildFile section */\n"
        f"\t\t{BUILD_FILE} /* IOKitTrapShim.m in Sources */ = "
        f"{{isa = PBXBuildFile; fileRef = {FILE_REF} /* IOKitTrapShim.m */; }};\n",
        1,
    )
    text = text.replace(
        "/* Begin PBXFileReference section */\n",
        "/* Begin PBXFileReference section */\n"
        f"\t\t{FILE_REF} /* IOKitTrapShim.m */ = {{isa = PBXFileReference; "
        "lastKnownFileType = sourcecode.c.objc; path = IOKitTrapShim.m; "
        'sourceTree = "<group>"; };\n',
        1,
    )
    print("file reference added")

    phase = text.find("isa = PBXSourcesBuildPhase;")
    if phase == -1:
        print("ERROR: no PBXSourcesBuildPhase")
        return text
    files = text.find("files = (", phase)
    if files == -1:
        print("ERROR: Sources phase has no files array")
        return text
    insert_at = text.index("\n", files) + 1
    text = (
        text[:insert_at]
        + f"\t\t\t\t{BUILD_FILE} /* IOKitTrapShim.m in Sources */,\n"
        + text[insert_at:]
    )
    print("added to Sources phase")
    return text


def main():
    write_sources()
    text = PROJ.read_text()
    text = set_ldflags(text)
    text = wire(text)
    PROJ.write_text(text)
    print("project patched")


if __name__ == "__main__":
    main()
