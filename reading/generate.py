#!/usr/bin/python3

import os
import re
from glob import glob
from dataclasses import dataclass
from typing import List

@dataclass
class ReadingItem:
    urls: List[str]
    tags: List[str]
    read: bool

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

    for r in raws:
        lines = [l.strip() for l in r.split("\n")]
        items.append(ReadingItem(urls=lines, tags=[], read=False))

    assert all(len(l.url) >= 1 for i in items)
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

        # TODO: User will implement the parser for .md files
        # For now, return empty list as placeholder

    return items

def generate_html(items: List[ReadingItem]):
    """Generate static HTML page from reading items."""

    # Separate read and unread items
    read_items = [item for item in items if item.read]
    unread_items = [item for item in items if not item.read]

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reading List</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .section {
            margin-bottom: 40px;
        }
        .item {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .urls {
            margin-bottom: 10px;
        }
        .url {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }
        .tags {
            font-size: 0.9em;
            color: #666;
        }
        .tag {
            background-color: #f0f0f0;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 5px;
            display: inline-block;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            border-bottom: 1px solid #555;
            padding-bottom: 5px;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
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
            for i, url in enumerate(item.urls):
                html_content += f'                <a href="{url}" class="url">Link {i+1}</a>\n'
            html_content += '            </div>\n'
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
            for i, url in enumerate(item.urls):
                html_content += f'                <a href="{url}" class="url">Link {i+1}</a>\n'
            html_content += '            </div>\n'
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
