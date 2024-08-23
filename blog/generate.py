#!/usr/bin/python3

import re
import os
import subprocess
from shlex import split
from os import chdir as cd
from os.path import splitext
from glob import glob
from sys import argv
from concurrent.futures import ThreadPoolExecutor, as_completed

only = argv[1] if len(argv) > 1 else None

stylefile = "../resources/style/pandoc.html"

run = lambda s: subprocess.run(split(s), check=True)

replace = "\s+.sourceCode {\s+background-color: transparent;\s+overflow: visible;\s+}"
repwith = "\n    .sourceCode {\n      font-size: 20px;\n    }"

def generate_article(i, f):
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

    return i, f

md_files = list(enumerate(glob('*.md'), 1))
if only:
    md_files = [(i, f) for i, f in md_files if i == int(only)]

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(generate_article, i, f) for i, f in md_files]
    
    for future in as_completed(futures):
        i, f = future.result()
        print(f"Generated article {i}: {f}")

