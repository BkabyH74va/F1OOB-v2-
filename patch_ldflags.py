import re, sys, pathlib

p = pathlib.Path("F1OOB.xcodeproj/project.pbxproj")
s = p.read_text()

LINE = ('\t\t\t\tOTHER_LDFLAGS = ("-framework", "UIKit", "-framework", '
        '"Foundation", "-framework", "IOKit", '
        '"-Wl,-undefined,dynamic_lookup");\n')

if '"UIKit"' in s:
    sys.exit("already has UIKit - nothing to do")

s, n = re.subn(r"\t+OTHER_LDFLAGS = \([^)]*\);\n", LINE, s)
if n == 0:
    s = re.sub(r"(buildSettings = \{\n)", r"\1" + LINE, s, count=2)
    print("inserted into both buildSettings blocks")
else:
    print(f"replaced {n} existing OTHER_LDFLAGS line(s)")

p.write_text(s)
print("done")
