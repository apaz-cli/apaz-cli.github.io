#!/usr/bin/python3

import re
import os
import subprocess
from shlex import split
from os import chdir as cd
from os.path import splitext
from glob import glob
from sys import argv
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

only = argv[1] if len(argv) > 1 else None

stylefile = "../resources/style/pandoc.html"

run = lambda s: subprocess.run(split(s), check=True)

replace = "\s+.sourceCode {\s+background-color: transparent;\s+overflow: visible;\s+}"
repwith = "\n    .sourceCode {\n      font-size: 20px;\n    }"


def generate_article(i, f):

    def replace_meta_with_opengraph(html):
        meta_rep = "  <!-- meta -->\n"
        titlegroup = re.search("<h1.*>(.*?)</h1>", html)
        subtitlegroup = re.search("<h4.*>(.*?)</h4>", html)
        first_image = re.search('<img.*src="(.*?)".*>', html)

        meta_with = ""
        if titlegroup:
            meta_with += f"  <meta name=\"og:title\" content=\"{titlegroup.group(1) if titlegroup else ''}\">\n"
            if subtitlegroup:
                meta_with += f"  <meta name=\"og:description\" content=\"{subtitlegroup.group(1) if subtitlegroup else ''}\">\n"
            if first_image:
                meta_with += f"  <meta name=\"og:image\" content=\"{first_image.group(1) if first_image else ''}\">\n"
        return html.replace(meta_rep, meta_with)

    title = splitext(f)[0]
    to = title + ".html"
    unstyled = title + "-unstyled.html"

    un = "_"
    sp = " "
    run(
        f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart -H {stylefile} {f} -o {to}'
    )
    run(
        f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart {f} -o {unstyled}'
    )

    with open(to, "r+") as tmp:
        stxt = tmp.read()
        txt = re.sub(replace, repwith, stxt, flags=re.DOTALL, count=1)
        txt = replace_meta_with_opengraph(txt)
        tmp.seek(0)
        tmp.write(txt)
        tmp.truncate()

    with open(unstyled, "r+") as tmp:
        stxt = tmp.read()
        txt = re.sub("\s+<style>.*</style>", "", stxt, flags=re.DOTALL, count=1)
        tmp.seek(0)
        tmp.write(txt)
        tmp.truncate()

    return i, f


md_files = list(enumerate(glob("*.md"), 1))
if only:
    md_files = [(i, f) for i, f in md_files if i == int(only)]

with ThreadPoolExecutor() as executor:
    futures = {executor.submit(generate_article, i, f): (i, f) for i, f in md_files}

    while futures:
        done, _ = concurrent.futures.wait(
            futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED
        )
        for future in done:
            i, f = future.result()
            print(f"Generated article {i}: {f}")
            futures.pop(future)
