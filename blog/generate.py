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
rss_description_max_length = 500  # Maximum length for RSS item descriptions

run = lambda s: subprocess.run(split(s), check=True)

replace = "\s+.sourceCode {\s+background-color: transparent;\s+overflow: visible;\s+}"
repwith = "\n    .sourceCode {\n      font-size: 20px;\n    }"

# Categories: list of (name, articles)
categories = [
  ("Programming", [
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
    "Thoughts_About_LLMs_Data_and_Optimization",
    "Thoughts_About_Entropy_and_Objectives",
  ]),
  ("SFW", [
    "Grifters",
    "Prompting",
  ]),
  ("NSFW", [
    "Seduction",
    "Revelations",
  ]),
  ("Mirrored", [
    "rat",
    "bml",
    "khome",
    "shirt",
  ]),
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

def get_description_from_html(f):
    STOP_TAGS = ['<pre', '<div class="sourceCode"', '<table', '<ul', '<ol']

    def clean_text(html):
        return re.sub(r'<[^>]+>', '', html).strip()

    def is_empty_para(content):
        return '<img' in content or clean_text(content) in ['', '<br>']

    def has_stop_tags(content):
        return any(tag in content for tag in STOP_TAGS)

    def truncate_if_needed(text):
        if len(text) > rss_description_max_length:
            return text[:rss_description_max_length - 3] + "..."
        return text

    with open(f, "r") as tmp:
        txt = tmp.read()

    # Extract and combine opening paragraphs
    body_match = re.search(r'<body>(.*?)</body>', txt, re.DOTALL)
    if not body_match:
        return ""

    combined = ""
    min_length = min(300, rss_description_max_length - 50)
    seen_title = False

    for match in re.finditer(r'<(h[1-6]|p)(?:[^>]*)?>.*?</\1>', body_match.group(1), re.DOTALL):
        tag = match.group(1)
        content = match.group(0)

        # Skip h1 title, then stop at any subsequent heading
        if tag.startswith('h'):
            if tag == 'h1' and not seen_title:
                seen_title = True
                continue
            if seen_title:
                break

        # Process text paragraphs only
        if tag == 'p':
            if is_empty_para(content):
                continue

            if has_stop_tags(content):
                if combined:
                    break
                continue

            text = clean_text(content)
            if not text:
                continue

            combined = f"{combined} {text}" if combined else text

            if len(combined) >= min_length:
                break

    return truncate_if_needed(combined) if combined else ""

def generate_article(i, f):

    def replace_meta_with_opengraph(html, filepath):
        rep_str = "  <title>"

        # Get the first h1 tag for title
        titlegroup = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        first_image = re.search(r'<img[^>]*src="([^"]*)"[^>]*>', html)

        meta_with = ""
        if titlegroup:
            title_content = re.sub(r'\s+', ' ', titlegroup.group(1).strip())
            meta_with += f"  <meta name=\"og:title\" content=\"{title_content}\">\n"

            # Use our smart description extraction
            description = get_description_from_html(filepath)
            if description:
                meta_with += f"  <meta name=\"og:description\" content=\"{description}\">\n"

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
    run(f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart -H {stylefile} {f} -o {to}')
    run(f'pandoc -s --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart {f} -o {unstyled}')

    with open(to, "r+") as tmp:
        stxt = tmp.read()
        txt = re.sub(replace, repwith, stxt, flags=re.DOTALL, count=1)
        txt = replace_meta_with_opengraph(txt, to)
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

    # Build lookup map from article name to category name
    article_to_category = {}
    for category_name, articles in categories:
        for article in articles:
            article_to_category[article] = category_name

    # Categorize posts
    categorized_posts = {category_name: [] for category_name, _ in categories}
    categorized_posts["Other"] = []

    for post in all_posts:
        post_basename = splitext(post[0])[0]
        category = article_to_category.get(post_basename, "Other")
        categorized_posts[category].append(post)

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

    # Output categories in order, then "Other"
    for category_name, _ in categories:
        posts = categorized_posts[category_name]
        if posts:
            idx_html += f"    <h2>{category_name.upper()}</h2>\n    <ul>\n"
            for post_file, post_title in posts:
                idx_html += f"        <li><a href=\"{post_file}\">{post_title}</a></li>\n"
            idx_html += "    </ul>\n"

    # Output "Other" category if it has posts
    if categorized_posts["Other"]:
        idx_html += f"    <h2>OTHER</h2>\n    <ul>\n"
        for post_file, post_title in categorized_posts["Other"]:
            idx_html += f"        <li><a href=\"{post_file}\">{post_title}</a></li>\n"
        idx_html += "    </ul>\n"

    idx_html += "</body>\n</html>"

    with open("index.html", "w") as f:
        f.write(idx_html)

def gen_rss():
    # Articles to exclude from RSS (NSFW and Mirrored)
    excluded_articles = {"Seduction", "Revelations", "rat", "bml", "khome", "shirt"}

    # Get all HTML files
    html_files = sorted([f for f in glob("*.html")
                         if not f.startswith("_")
                         and f != "index.html"
                         and not f.endswith("-unstyled.html")])

    # Filter out excluded articles
    rss_items = []
    for f in html_files:
        basename = splitext(f)[0]
        if basename in excluded_articles:
            continue

        title = get_title_from_html(f)
        description = get_description_from_html(f)

        # Escape XML special characters
        title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        description = description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        rss_items.append((f, title, description))

    # Generate RSS feed
    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Blog Posts</title>
    <link>https://apaz-cli.github.io/blog/</link>
    <description>Programming and thoughts</description>
    <atom:link href="https://apaz-cli.github.io/blog/index.rss" rel="self" type="application/rss+xml" />
"""

    for filename, title, description in rss_items:
        link = f"https://apaz-cli.github.io/blog/{filename}"
        rss += f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid>{link}</guid>
"""
        if description:
            rss += f"      <description>{description}</description>\n"
        rss += "    </item>\n"

    rss += """  </channel>
</rss>"""

    with open("index.rss", "w") as f:
        f.write(rss)

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

with ThreadPoolExecutor() as executor:
    index_future = executor.submit(gen_index)
    rss_future = executor.submit(gen_rss)

    index_future.result()
    print("Generated index.html")

    rss_future.result()
    print("Generated index.rss")
