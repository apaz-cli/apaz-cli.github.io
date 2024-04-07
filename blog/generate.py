#!/usr/bin/python3

import re
import os
import subprocess
from shlex import split
from os import chdir as cd
from os.path import splitext
from glob import glob
from sys import argv

only = argv[1] if len(argv) > 1 else None

stylefile = "../resources/style/pandoc.html"

run = lambda s: subprocess.run(split(s), check=True)

replace = "\s+.sourceCode {\s+background-color: transparent;\s+overflow: visible;\s+}"
repwith = "\n    .sourceCode {\n      font-size: 20px;\n    }"

for i, f in enumerate(glob('*.md')):
    i += 1
    if only and not i == int(only):
        continue

    un="_";sp=" "

    title = splitext(f)[0]
    to = title + '.html'
    unstyled = title + "-unstyled.html"

    run(f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart -H {stylefile} {f} -o {to}')
    run(f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart {f} -o {unstyled}')

    with open(to, 'r+') as tmp:
        stxt = tmp.read()
        txt = re.sub(replace, repwith, stxt, flags=re.DOTALL, count=1)
        tmp.seek(0)
        tmp.write(txt)
        tmp.truncate()

    with open(unstyled, 'r+') as tmp:
        stxt = tmp.read()
        txt = re.sub("\s+<style>.*</style>", "", stxt, flags=re.DOTALL, count=1)
        tmp.seek(0)
        tmp.write(txt)
        tmp.truncate()

    print(f"Generated article {i}: {f}")

