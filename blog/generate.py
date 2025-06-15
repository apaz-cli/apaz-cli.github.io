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

# Categories
prog_posts = [
  "Hyperparameter_Heuristics",
  "Cursed_Code_Collection",
  "How_to_Write_a_Compiler_Without_Going_Insane",
  "Safety_and_Correctness",
  "LLM_Code_Optimization",
  "The_Contributor_Competition",
  "The_Craziest_Bug_I_Have_Ever_Witnessed",
  "Descending_Into_The_Stack_And_Madness",
]
nsfw_posts = [
  "Seduction",
  "Revelations",
  "rat",
  "bml",
]

def get_title_from_html(f):
    try:
        with open(f, "r") as tmp:
            txt = tmp.read()
            title_match = re.search("<title>(.*?)</title>", txt)
            h1_match = re.search("<h1.*?>(.*?)</h1>", txt)
            return (h1_match or title_match).group(1) if (h1_match or title_match) else splitext(f)[0]
    except:
        return splitext(f)[0]

def generate_article(i, f):

    def replace_meta_with_opengraph(html):
        rep_str = "  <title>"

        # Use content to generate opengraph meta tags.
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
        meta_with += rep_str
        return html.replace(rep_str, meta_with)

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

def gen_index():
    md_basenames = {splitext(f)[0] for f in glob("*.md") if not f.startswith("_")}
    html_files = [f for f in glob("*.html") if not f.startswith("_") and f != "index.html" and not f.endswith("-unstyled.html")]
    html_only = [f for f in html_files if splitext(f)[0] not in md_basenames]

    all_posts = [(splitext(f)[0] + ".html", get_title_from_html(f)) for f in html_files]

    categorize = lambda p: ("programming" if splitext(p[0])[0] in prog_posts else "nsfw" if splitext(p[0])[0] in nsfw_posts else "sfw")

    cats = {"programming": [], "sfw": [], "nsfw": [], }
    for post in all_posts:
        cats[categorize(post)].append(post)

    idx_html = "<!DOCTYPE html>\n<html>\n<head>\n    <title>Blog Index</title>\n</head>\n<body>\n    <h1>Blog Posts</h1>\n"

    for cat, posts in cats.items():
        if posts:
            idx_html += f"    <h2>{cat.upper()}</h2>\n    <ul>\n"
            for post_file, post_title in posts:
                idx_html += f"        <li><a href=\"{post_file}\">{post_title}</a></li>\n"
            idx_html += "    </ul>\n"

    idx_html += "</body>\n</html>"

    with open("index.html", "w") as f:
        f.write(idx_html)

md_files: list[tuple[int, str]] = list(enumerate([f for f in glob("*.md") if not f.startswith("_")], 1))
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

gen_index()
print("Generated index.html")
