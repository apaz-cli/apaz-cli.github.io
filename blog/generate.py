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
  "PerfWizard",
  "A_Treatise_On_ML_Data_Infrastructure",
]
nsfw_posts = [
  "Seduction",
  "Revelations",
]
mirrored_posts = [
  "rat",
  "bml",
  "khome",
  "shirt",
]

def get_title_from_html(f):
    with open(f, "r") as tmp:
        txt = tmp.read()
        title_match = re.search("<title>(.*?)</title>", txt)
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", txt, re.DOTALL)
        if h1_match:
            return re.sub(r'\s+', ' ', h1_match.group(1).strip())
        elif title_match:
            return re.sub(r'\s+', ' ', title_match.group(1).strip())
        else:
            return splitext(f)[0]

def generate_article(i, f):

    def replace_meta_with_opengraph(html):
        rep_str = "  <title>"

        # Use content to generate opengraph meta tags.
        # Get the first h1 tag specifically
        titlegroup = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        subtitlegroup = re.search(r"<h4[^>]*>(.*?)</h4>", html, re.DOTALL)
        first_image = re.search(r'<img[^>]*src="([^"]*)"[^>]*>', html)

        meta_with = ""
        if titlegroup:
            title_content = re.sub(r'\s+', ' ', titlegroup.group(1).strip())  # Replace newlines/multiple spaces with single space
            meta_with += f"  <meta name=\"og:title\" content=\"{title_content}\">\n"
            if subtitlegroup:
                subtitle_content = re.sub(r'\s+', ' ', subtitlegroup.group(1).strip())  # Clean up subtitle too
                meta_with += f"  <meta name=\"og:description\" content=\"{subtitle_content}\">\n"
            if first_image:
                image_src = first_image.group(1)
                meta_with += f"  <meta name=\"og:image\" content=\"{image_src}\">\n"
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
    html_files = sorted([f for f in glob("*.html") if not f.startswith("_") and f != "index.html" and not f.endswith("-unstyled.html")])
    html_only = sorted([f for f in html_files if splitext(f)[0] not in md_basenames])

    all_posts = sorted([(splitext(f)[0] + ".html", get_title_from_html(f)) for f in html_files])

    categorize = lambda p: ("programming" if splitext(p[0])[0] in prog_posts else
                           "nsfw" if splitext(p[0])[0] in nsfw_posts else
                           "mirrored" if splitext(p[0])[0] in mirrored_posts else
                           "sfw")

    cats = {"programming": [], "sfw": [], "nsfw": [], "mirrored": []}
    for post in all_posts:
        cats[categorize(post)].append(post)

    # Read CSS from pandoc.html
    css_content = ""
    with open(stylefile, "r") as css_file:
        css_content = css_file.read()

    idx_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Blog Index</title>
{css_content}
</head>
<body>
    <h1>Blog Posts</h1>
    <img src="images/100439997_p0.jpg" style="display: block; margin: 0 auto;" height=400>
"""

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
