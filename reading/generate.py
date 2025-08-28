#!/usr/bin/python3

import os
import re
import time
import requests
from glob import glob
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

_last_request_time = 0  # Rate limiting for arXiv requests


@dataclass
class ReadingItem:
    name: str
    urls: List[str]
    tags: List[str]
    read: bool
    abstract: Optional[str] = None

def parse_list_txt() -> List[ReadingItem]:
    """Parse list.txt file containing unread items."""
    items = []
    if not os.path.exists('list.txt'):
        return items

    with open('list.txt', 'r') as f:
        content = f.read().strip()

    if not content:
        raise ValueError("list.txt is empty.")

    raws = [l.strip() for l in re.split(r'#\s', content)]
    if raws[0].strip() == "":
        raws.pop(0)

    for r in raws:
        urls = []
        lines = [l.strip() for l in r.split("\n")]
        lines = [l for l in lines if l]

        # If the line is an arxiv link, get the name and abstract.
        first_url = None
        if lines[0].startswith("http"):
            first_url = lines.pop(0)
            urls.append(first_url)
        
        # If we have a URL, try to get info from it, otherwise use first line as name
        if first_url is not None:
            name, abstract = get_info_from_url(first_url)
            if name is None:
                raise ValueError(f"Could not get info for first URL: {first_url}")
        else:
            # TODO: Add the ability to specify abstracts for non-arxiv links.
            name, abstract = lines.pop(0), None

        # Get the rest of the URLs
        while len(lines) > 0 and lines[0].startswith("http"):
            urls.append(lines.pop(0))

        # Parse Tags
        tags = []
        while (len(lines) > 0) and (lines[0].startswith("*")):
          l = lines.pop(0)
          tgs = l.split("*")
          tgs = [t.strip() for t in tgs if t]
          tags.extend(tgs)
        tags = sorted(list(set(tags)))
        
        assert len(lines) == 0
        assert len(urls) >= 1
        assert all(u.startswith("http") for u in urls)

        items.append(ReadingItem(name=name, urls=urls, tags=tags, read=False, abstract=abstract))
        print(f"Added \"{name}\" to reading list.")

    assert all(len(i.urls) >= 1 for i in items)

    for r in items:
        print(r.name, r.urls, r.tags, r.read, bool(r.abstract))

    return items

def parse_md_files() -> List[ReadingItem]:
    """Parse all .md files containing read items."""
    items = []
    md_files = glob('*.md')

    for md_file in md_files:
        with open(md_file, 'r') as f:
            content = f.read().strip()

        if not content:
            continue

        # TODO: Implement

    return items

def get_arxiv_id(url: str) -> re.Match[str] | None:
    """Check if a URL is an arXiv URL. and return the matches for the arXiv ID."""
    arxiv_pattern = r'arxiv\.org/(?:abs|pdf|html)/(.+?)(?:\?|$)'
    return re.search(arxiv_pattern, url)

def get_info_from_url(url: str | None) -> tuple[Optional[str], Optional[str]]:
    """Scrape arXiv paper title and abstract from URL with rate limiting (5 requests/second).
    Returns (title, abstract)"""
    global _last_request_time

    if url is None:
        return None, None
    match = get_arxiv_id(url)
    if not match:
        return None, None

    arxiv_id = match.group(1)
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    # Rate limiting: ensure at least 0.2 seconds between requests (5 req/sec)
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    if time_since_last < 0.2:
        time.sleep(0.2 - time_since_last)

    try:
        response = requests.get(abs_url, timeout=10)
        response.raise_for_status()
        _last_request_time = time.time()

        title = None
        abstract = None

        # Extract title from the page
        title_match = re.search(r'<meta name="citation_title" content="([^"]+)"', response.text)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback: look for title in h1 tag
            title_match = re.search(r'<h1[^>]*class="title[^"]*"[^>]*>.*?<span[^>]*>(.*?)</span>', response.text, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'\s+', ' ', title)

        # Extract abstract
        abstract_match = re.search(r'<blockquote[^>]*class="abstract[^"]*"[^>]*>.*?<span[^>]*>Abstract:</span>(.*?)</blockquote>', response.text, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            abstract = re.sub(r'\s+', ' ', abstract)

        return title, abstract

    except Exception as e:
        print(f"Error fetching arXiv paper {arxiv_id}: {e}")
        return None, None


def generate_html(items: List[ReadingItem]):
    """Generate static HTML page from reading items."""

    # Separate read and unread items
    read_items = [item for item in items if item.read]
    unread_items = [item for item in items if not item.read]

    # Read CSS from pandoc.html like blog/generate.py does
    stylefile = "../resources/style/pandoc.html"
    css_content = ""
    with open(stylefile, "r") as css_file:
        css_content = css_file.read()

    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>apaz's Reading List</title>
{css_content}

<style>
        @font-face {{
            font-family: "lemon";
            src: url('../resources/style/lemon.woff');
        }}
        body {{
            margin: 6rem auto 1rem;
            padding: .25rem;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .item {{
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #444;
            border-radius: 5px;
            background-color: #333;
        }}
        h3 {{
            font-family: "lemon";
        }}
        details {{
            margin-top: 10px;
        }}
        summary {{
            cursor: pointer;
            color: #01ff70;
            font-size: 0.9em;
            padding: 5px 0;
        }}
        summary:hover {{
            color: #2ecc40;
        }}
        .abstract {{
            margin-top: 10px;
            padding: 10px;
            background-color: #444;
            border-left: 3px solid #01ff70;
            font-style: italic;
            color: #ccc;
        }}
        .urls {{
            margin-bottom: 10px;
        }}
        .url {{
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }}
        .tags {{
            font-size: 0.9em;
            color: #999;
        }}
        .tag {{
            background-color: #555;
            color: #fafafa;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 5px;
            display: inline-block;
        }}
</style>

</head>
<body>
    <h1>Reading List</h1>
'''

    if unread_items:
        html_content += '''
    <div class="section">
        <h2>To Read</h2>
'''
        for item in unread_items:
            html_content += '        <div class="item">\n'
            html_content += '            <div class="urls">\n'
            html_content += f'                <h3>{item.name}</h3>\n'
            for i, url in enumerate(item.urls):
                html_content += f'                <a href="{url}" class="url" target="_blank">{url}</a>\n'
            html_content += '            </div>\n'
            if item.abstract:
                html_content += '            <details>\n'
                html_content += '                <summary>Abstract</summary>\n'
                html_content += f'                <div class="abstract">{item.abstract}</div>\n'
                html_content += '            </details>\n'
            if item.tags:
                html_content += '            <div class="tags">\n'
                for tag in item.tags:
                    html_content += f'                <span class="tag">{tag}</span>\n'
                html_content += '            </div>\n'
            html_content += '        </div>\n'
        html_content += '    </div>\n'

    if read_items:
        html_content += '''
    <div class="section">
        <h2>Read</h2>
'''
        for item in read_items:
            html_content += '        <div class="item">\n'
            html_content += '            <div class="urls">\n'
            html_content += f'                <h3>{item.name}</h3>\n'
            for i, url in enumerate(item.urls):
                html_content += f'                <a href="{url}" class="url" target="_blank">Link {i+1}</a>\n'
            html_content += '            </div>\n'
            if item.abstract:
                html_content += '            <details>\n'
                html_content += '                <summary>Show Abstract</summary>\n'
                html_content += f'                <div class="abstract">{item.abstract}</div>\n'
                html_content += '            </details>\n'
            if item.tags:
                html_content += '            <div class="tags">\n'
                for tag in item.tags:
                    html_content += f'                <span class="tag">{tag}</span>\n'
                html_content += '            </div>\n'
            html_content += '        </div>\n'
        html_content += '    </div>\n'

    html_content += '''
</body>
</html>'''

    with open('index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    # Parse unread items from list.txt
    unread_items = parse_list_txt()

    # Parse read items from .md files
    read_items = parse_md_files()

    # Combine all items
    all_items = unread_items + read_items

    # Generate HTML page
    generate_html(all_items)

    print(f"Generated reading list with {len(unread_items)} unread and {len(read_items)} read items.")
