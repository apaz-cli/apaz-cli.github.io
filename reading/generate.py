#!/usr/bin/python3

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from glob import glob

import requests


# Global rate limiter for arXiv requests
_arxiv_rate_limiter_lock = threading.Lock()
_arxiv_last_request_time = 0.0
_arxiv_min_interval = 1.0 / 5.0  # 5 requests per second

def arxiv_rate_limit(func):
    """Decorator to rate limit arXiv requests across all functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _arxiv_last_request_time
        with _arxiv_rate_limiter_lock:
            current_time = time.time()
            time_since_last = current_time - _arxiv_last_request_time
            if time_since_last < _arxiv_min_interval:
                time.sleep(_arxiv_min_interval - time_since_last)
            _arxiv_last_request_time = time.time()
        return func(*args, **kwargs)
    return wrapper


def parse_published_date(date_str: str | None) -> datetime | None:
    """Parse published date string (format: '31 Aug 2025') to datetime object."""
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, '%d %b %Y')
    except ValueError:
        return None


@dataclass
class ReadingItem:
    name: str
    urls: list[str]
    tags: list[str]
    read: bool
    summary: str | None = None
    abstract: str | None = None
    published_date: str | None = None

def process_txt_item(index_and_raw, keep_pdfs=False):
    """Process a single raw item and return (index, ReadingItem)."""
    index, r = index_and_raw
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
        name, abstract, published_date = get_info_from_url(first_url)
        if name is None:
            raise ValueError(f"Could not get title from URL: {first_url}. Add a title line before the URL.")
    else:
        # TODO: Add the ability to specify abstracts for non-arxiv links.
        name, abstract, published_date = lines.pop(0), None, None

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

    # The rest is the summary.
    summary = "\n".join(lines).strip()
    read = summary != ""

    assert len(urls) >= 1
    assert all(u.startswith("http") for u in urls)

    item = ReadingItem(name=name, urls=urls, tags=tags, read=read, summary=summary, abstract=abstract, published_date=published_date)

    # Generate image for papers (arXiv or direct PDF links)
    identifier, id_type = get_paper_identifier(urls[0])
    if id_type != 'none':
        download_pdf_and_extract_image(urls[0], keep_pdf=keep_pdfs, paper_name=name)

    print(f"Added \"{name}\" to reading list.")

    return (index, item)

def parse_list(keep_pdfs: bool = False) -> list[ReadingItem]:
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

    # Process items in parallel while maintaining order
    with ThreadPoolExecutor() as executor:
        # Submit all tasks with their original indices
        indexed_raws = list(enumerate(raws))
        futures = {executor.submit(process_txt_item, indexed_raw, keep_pdfs): indexed_raw[0] for indexed_raw in indexed_raws}

        # Collect results
        results = []
        for future in as_completed(futures):
            results.append(future.result())

        # Sort by original index to maintain order
        results.sort(key=lambda x: x[0])
        items = [item for _, item in results]

    # Assert there were no duplicate URLs
    seen_urls = set()
    for item in items:
        for url in item.urls:
            if url in seen_urls:
                raise ValueError(f"Duplicate URL found: {url}")
            seen_urls.add(url)

    assert all(len(i.urls) >= 1 for i in items)
    return items

def get_arxiv_id(url: str) -> re.Match[str] | None:
    """Check if a URL is an arXiv URL. and return the matches for the arXiv ID."""
    arxiv_pattern = r'arxiv\.org/(?:abs|pdf|html)/(.+?)(?:\?|$)'
    return re.search(arxiv_pattern, url)

def get_paper_identifier(url: str) -> tuple[str | None, str]:
    """Get identifier for a paper URL.

    Returns:
        tuple[identifier, type] where type is 'arxiv', 'hash', or 'none'
    """
    arxiv_match = get_arxiv_id(url)
    if arxiv_match:
        return arxiv_match.group(1), 'arxiv'
    elif url.endswith('.pdf'):
        return hashlib.md5(url.encode()).hexdigest()[:12], 'hash'
    return None, 'none'

def get_cache_path(url: str) -> str:
    """Generate cache file path for a URL."""
    cache_dir = "/tmp/arxiv_cache"
    os.makedirs(cache_dir, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"{cache_dir}/{url_hash}.json"

def get_image_paths(identifier: str) -> tuple[str, str]:
    """Generate thumbnail and full-size image file paths for a paper identifier."""
    image_dir = "paper_images"
    os.makedirs(image_dir, exist_ok=True)
    # Replace problematic characters in identifier for filename
    safe_id = re.sub(r'[^\w\-_\.]', '_', identifier)
    thumbnail_path = f"{image_dir}/{safe_id}_thumb.png"
    fullsize_path = f"{image_dir}/{safe_id}.png"
    return thumbnail_path, fullsize_path

def get_pdf_url(arxiv_id: str) -> str:
    """Generate PDF URL for an arXiv ID."""
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"

def pdf_to_images(pdf_path: str, identifier: str, thumbnail_path: str, fullsize_path: str) -> bool:
    """Convert PDF first page to thumbnail and full-size PNG images using ghostscript.
    Returns True if successful, False otherwise."""
    try:
        # Generate thumbnail (160px width, proportional height)
        thumbnail_cmd = [
            'gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=png16m',
            '-r200',
            '-dFirstPage=1', '-dLastPage=1',
            '-dFIXEDMEDIA', '-dPDFFitPage',
            '-g100x150',
            f'-sOutputFile={thumbnail_path}',
            pdf_path
        ]
        subprocess.run(thumbnail_cmd, check=True, capture_output=True)

        # Generate full-size image (higher resolution)
        fullsize_cmd = [
            'gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=png16m',
            '-r200',
            '-dFirstPage=1', '-dLastPage=1',
            f'-sOutputFile={fullsize_path}',
            pdf_path
        ]
        subprocess.run(fullsize_cmd, check=True, capture_output=True)

        print(f"Generated thumbnail and full-size images for {identifier}")
        return True

    except Exception as e:
        print(f"Error converting PDF to images for {identifier}: {e}")
        # Clean up any partial files
        for img_file in [thumbnail_path, fullsize_path]:
            if os.path.exists(img_file):
                os.remove(img_file)
        return False


def get_raw_pdf_url(url: str) -> str:
    """Convert GitHub blob URLs to raw URLs for direct PDF access."""
    if 'github.com' in url and '/blob/' in url:
        return url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    return url

def create_safe_pdf_filename(paper_name: str, identifier: str) -> str:
    """Create a safe filename for PDF caching using paper name and identifier."""
    # Clean the paper name to avoid filesystem issues
    safe_name = re.sub(r'[<>:"/\\|?*]', '', paper_name)  # Remove filesystem-unsafe chars
    safe_name = re.sub(r'\s+', ' ', safe_name.strip())  # Normalize whitespace
    if len(safe_name) > 100:
        safe_name = safe_name[:100].strip()
    return f"{safe_name} [{identifier}].pdf"

def download_pdf_and_extract_image(url: str, keep_pdf: bool = False, paper_name: str | None = None) -> tuple[str, str] | None:
    """Download PDF from URL and convert first page to thumbnail and full-size PNG images.
    Works with both arXiv URLs and direct PDF URLs.

    Args:
        url: The URL to download the PDF from
        keep_pdf: If True, save the PDF in the cache directory for later reading
        paper_name: Name of the paper for readable filename

    Returns tuple of (thumbnail_path, fullsize_path), or None if failed."""

    # Get paper identifier and determine processing approach
    identifier, id_type = get_paper_identifier(url)
    if id_type == 'none':
        return None

    assert isinstance(identifier, str)
    if id_type == 'arxiv':
        pdf_url = get_pdf_url(identifier)
        rate_limited_download = arxiv_rate_limit(lambda: requests.get(pdf_url, timeout=30))
    else:  # hash type (direct PDF)
        pdf_url = get_raw_pdf_url(url)  # Convert GitHub URLs to raw format
        rate_limited_download = lambda: requests.get(pdf_url, timeout=30)  # No rate limiting for non-arXiv

    thumbnail_path, fullsize_path = get_image_paths(identifier)

    # Skip if both images already exist
    if os.path.exists(thumbnail_path) and os.path.exists(fullsize_path):
        return thumbnail_path, fullsize_path

    try:
        # Download PDF to temporary file
        pdf_response = rate_limited_download()
        pdf_response.raise_for_status()

        temp_pdf = f"/tmp/{identifier}.pdf"
        with open(temp_pdf, 'wb') as f:
            f.write(pdf_response.content)

        # Convert PDF to images
        success = pdf_to_images(temp_pdf, identifier, thumbnail_path, fullsize_path)

        # Save PDF to cache if requested and conversion was successful
        if keep_pdf and success and paper_name:
            cache_dir = "/tmp/arxiv_cache"
            os.makedirs(cache_dir, exist_ok=True)

            # Create readable filename
            safe_filename = create_safe_pdf_filename(paper_name, identifier)
            cached_pdf_path = f"{cache_dir}/{safe_filename}"

            # Also check for old-style filename to avoid duplicates
            old_style_path = f"{cache_dir}/{identifier}.pdf"

            # Only copy if neither filename exists
            if not os.path.exists(cached_pdf_path) and not os.path.exists(old_style_path):
                shutil.copy2(temp_pdf, cached_pdf_path)
                print(f"Saved PDF to cache: {cached_pdf_path}")
            elif os.path.exists(old_style_path) and not os.path.exists(cached_pdf_path):
                # Rename old-style file to new format
                shutil.move(old_style_path, cached_pdf_path)
                print(f"Renamed PDF in cache: {cached_pdf_path}")

        # Clean up temporary PDF
        os.remove(temp_pdf)

        if success:
            return thumbnail_path, fullsize_path
        else:
            return None

    except Exception as e:
        print(f"Error processing PDF for {identifier}: {e}")
        # Clean up any temporary files
        for temp_file in [f"/tmp/{identifier}.pdf", thumbnail_path, fullsize_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

def load_from_cache(url: str) -> tuple[str | None, str | None, str | None]:
    """Load title, abstract, and published_date from cache if available."""
    cache_path = get_cache_path(url)
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return data.get('title'), data.get('abstract'), data.get('published_date')
    except Exception as e:
        print(f"Error reading cache for {url}: {e}")
    return None, None, None

def save_to_cache(url: str, title: str | None, abstract: str | None, published_date: str | None):
    """Save title, abstract, and published_date to cache."""
    cache_path = get_cache_path(url)
    try:
        data = {'title': title, 'abstract': abstract, 'published_date': published_date}
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing cache for {url}: {e}")

def get_info_from_url(url: str | None) -> tuple[str | None, str | None, str | None]:
    """Scrape arXiv paper title, abstract, and published date from URL with rate limiting (5 requests/second).
    Returns (title, abstract, published_date)"""
    if url is None:
        return None, None, None
    match = get_arxiv_id(url)
    if not match:
        return None, None, None

    arxiv_id = match.group(1)
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    # Check cache first
    cached_title, cached_abstract, cached_published_date = load_from_cache(abs_url)
    if cached_title is not None or cached_abstract is not None:
        return cached_title, cached_abstract, cached_published_date

    @arxiv_rate_limit
    def fetch_arxiv_page():
        return requests.get(abs_url, timeout=10)

    try:
        response = fetch_arxiv_page()
        response.raise_for_status()

        title = None
        abstract = None
        published_date = None

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

        # Extract published date
        # Look for submission date in format "Submitted on 31 Aug 2025"
        date_match = re.search(r'Submitted on (\d{1,2} \w{3} \d{4})', response.text)
        if date_match:
            published_date = date_match.group(1)

        if title is not None and abstract is not None:
            title = title.replace("$\\mu$", "μ")
            abstract = abstract.replace("$\\mu$", "μ")
            save_to_cache(abs_url, title, abstract, published_date)

        return title, abstract, published_date

    except Exception as e:
        print(f"Error fetching arXiv paper {arxiv_id}: {e}")
        return None, None, None


def generate_html(items: list[ReadingItem]):
    """Generate static HTML page from reading items."""

    # Sort items: read items first, then by published date (most recent first)
    # Items without published dates go to the end within their category
    def sort_key(item):
        date_obj = parse_published_date(item.published_date)
        date_value = date_obj if date_obj else datetime.min
        # Return tuple: (read status as negative for reverse order, date)
        return (-date_value.timestamp() if date_obj else 0)

    items.sort(key=sort_key)

    # Inject CSS styles
    stylefile = "../resources/style/pandoc.html"
    css_content = ""
    with open(stylefile, "r") as css_file:
        css_content = css_file.read()

    # Collect all unique tags
    all_tags = set()
    for item in items:
        all_tags.update(item.tags)
    all_tags = sorted(list(all_tags))

    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>apaz's Reading List</title>
    <link rel="icon" type="image/png" href="../resources/images/favicon.png">
{css_content}

<style>
        @font-face {{
            font-family: "lemon";
            src: url('../resources/style/lemon.woff');
        }}
        body {{
            margin: 6rem auto 1rem;
            padding: .25rem;
            max-width: 90rem;
            background-color: transparent;
        }}
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('../resources/images/patchoulli.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            opacity: 0.1;
            z-index: -1;
        }}
        .filter-controls {{
            float: right;
            margin-bottom: 0;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .section-header h2 {{
            margin: 0;
        }}
        .filter-controls select, .filter-controls input {{
            background-color: rgba(51, 51, 51, 0.8);
            color: #fafafa;
            border: 1px solid #444;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 1rem;
            margin-right: 15px;
        }}
        .filter-controls input::placeholder {{
            color: #999;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .item {{
            padding: 15px;
            border: 1px solid #444;
            border-radius: 5px;
            background-color: rgba(51, 51, 51, 0.8);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }}
        .item.hidden {{
            display: none;
        }}
        .item.read {{
            border-left: 4px solid #01ff70;
            background-color: rgba(51, 51, 51, 0.9);
        }}
        @media (max-width: 1200px) {{
            .grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
        h2 {{
            color: #00bb00;
        }}
        h3 {{
            font-family: "lemon";
            color: rgb(112, 221, 0);
            margin-top: 0;
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
            background-color: rgba(68, 68, 68, 0.8);
            border-left: 3px solid #01ff70;
            font-style: italic;
            color: #ccc;
        }}
        .summary {{
            margin-top: 10px;
            padding: 10px;
            background-color: rgba(68, 68, 68, 0.8);
            border-left: 3px solid #01ff70;
            color: #ccc;
            white-space: pre-wrap;
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
            margin-top: auto;
            padding-top: 10px;
        }}
        .tag {{
            background-color: #555;
            color: #fafafa;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 5px;
            display: inline-block;
        }}
        .paper-image {{
            position: absolute;
            bottom: 15px;
            right: 15px;
            max-width: 120px;
            max-height: 180px;
            border: 1px solid #666;
            border-radius: 3px;
            opacity: 1;
            transition: transform 0.3s ease;
            cursor: pointer;
        }}
        .paper-image:hover {{
            transform: scale(1.05);
            transition: all 0.2s ease;
        }}
        .item details[open] ~ .paper-image {{
            opacity: 0;
            pointer-events: none;
        }}
        .image-modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            justify-content: center;
            align-items: center;
        }}
        .image-modal.show {{
            display: flex;
        }}
        .modal-content {{
            max-width: 90%;
            max-height: 90%;
            border-radius: 5px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }}
        .close-modal {{
            position: absolute;
            top: 20px;
            right: 35px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }}
        .close-modal:hover {{
            color: #01ff70;
        }}
</style>

</head>
<body>
    <h1>apaz's Reading List</h1>
    <p>These are a bunch papers, sites, repos, etc that have caught my attention, which I want to do more with.</p>
    <p>This list is incomplete, but I think every resource here is worth a read or a skim. It's a truly insane amount of reading, probably don't read too closely, but I think it's worth understanding at least what's in them.</p>
    <p>As I read more closely and implement more stuff I'll be leaving notes on my impressions. If anything I say is incorrect or you have something to add, please yell at me on <a href="https://x.com/apaz_cli">twitter</a> or <a href="https://discord.com/invite/gpumode">discord</a>.</p>
'''

    html_content += '''
    <div class="section">
        <div class="section-header">
            <h2>Reading List</h2>
            <div class="filter-controls">
                <label for="search-bar">Search: </label>
                <input type="text" id="search-bar" placeholder="Search papers..." />
                <label for="tag-filter">Filter by tag: </label>
                <select id="tag-filter">
                    <option value="">All</option>
'''
    for tag in all_tags:
        html_content += f'                    <option value="{tag}">{tag}</option>\n'

    html_content += '''                </select>
            </div>
        </div>
        <div class="grid">
'''
    for item in items:
        tags_attr = ' '.join(item.tags) if item.tags else ''
        read_class = ' read' if item.read else ''
        html_content += f'            <div class="item{read_class}" data-tags="{tags_attr}">\n'
        html_content += '                <div class="urls">\n'
        html_content += f'                    <h3>{item.name}</h3>\n'
        for i, url in enumerate(item.urls):
            if item.read:
                html_content += f'                    <a href="{url}" class="url" target="_blank">Link {i+1}</a>\n'
            else:
                html_content += f'                    <a href="{url}" class="url" target="_blank">{url}</a>\n'
        html_content += '                </div>\n'
        if item.abstract:
            html_content += '                <details class="abstract-details">\n'
            html_content += '                    <summary>Abstract</summary>\n'
            html_content += f'                    <div class="abstract">{item.abstract}</div>\n'
            html_content += '                </details>\n'
        if item.summary and item.read:
            html_content += '                <details class="notes">\n'
            html_content += '                    <summary>Notes</summary>\n'
            html_content += f'                    <div class="summary">{item.summary}</div>\n'
            html_content += '                </details>\n'
        if item.tags:
            html_content += '                <div class="tags">\n'
            for tag in item.tags:
                html_content += f'                    <span class="tag">{tag}</span>\n'
            html_content += '                </div>\n'

        # Add paper thumbnail if available
        for url in item.urls:
            identifier, id_type = get_paper_identifier(url)

            if id_type != 'none' and identifier:
                thumbnail_path, fullsize_path = get_image_paths(identifier)
                if os.path.exists(thumbnail_path):
                    html_content += f'                <img src="{thumbnail_path}" data-fullsize="{fullsize_path}" class="paper-image" alt="Paper preview">\n'
                break

        html_content += '            </div>\n'
    html_content += '        </div>\n'
    html_content += '    </div>\n'

    html_content += '''
    <script>
        // No further JavaScript is allowed beyond this point
        document.addEventListener('DOMContentLoaded', function() {
            const details = document.querySelectorAll('details');
            const tagFilter = document.getElementById('tag-filter');
            const searchBar = document.getElementById('search-bar');

            // Reset filter selection on page load
            if (tagFilter) tagFilter.value = '';
            if (searchBar) searchBar.value = '';

            // Simple substring matching function
            function searchMatch(needle, haystack) {
                if (needle === '') return true;
                return haystack.toLowerCase().includes(needle.toLowerCase());
            }

            // Get searchable text from an item
            function getSearchableText(item) {
                const title = item.querySelector('h3').textContent;
                const tags = item.getAttribute('data-tags') || '';
                const abstract = item.querySelector('.abstract');
                const abstractText = abstract ? abstract.textContent : '';
                return (title + ' ' + tags + ' ' + abstractText).toLowerCase();
            }

            // Combined filtering function
            function filterItems() {
                const searchTerm = searchBar.value.trim();
                const selectedTag = tagFilter.value;
                const items = document.querySelectorAll('.item');

                items.forEach(item => {
                    let showItem = true;

                    // Tag filtering
                    if (selectedTag !== '') {
                        const itemTags = item.getAttribute('data-tags');
                        showItem = showItem && itemTags && itemTags.includes(selectedTag);
                    }

                    // Search filtering
                    if (searchTerm !== '' && showItem) {
                        const searchableText = getSearchableText(item);
                        showItem = showItem && searchMatch(searchTerm, searchableText);
                    }

                    if (showItem) {
                        item.classList.remove('hidden');
                    } else {
                        item.classList.add('hidden');
                    }
                });
            }

            // Event listeners for filtering
            if (tagFilter) tagFilter.addEventListener('change', filterItems);
            if (searchBar) searchBar.addEventListener('input', filterItems);

            // Row toggle functionality for details and image hiding
            details.forEach(detail => {
                detail.addEventListener('toggle', function() {
                    // Only sync abstract details across rows, not notes
                    if (!this.classList.contains('abstract-details')) {
                        return;
                    }

                    // Find the parent item and then the parent grid
                    const item = this.closest('.item');
                    const grid = item.closest('.grid');

                    // Get all visible items in the same grid
                    const allItems = Array.from(grid.querySelectorAll('.item:not(.hidden)'));
                    const currentIndex = allItems.indexOf(item);

                    // Calculate which row this item is in (assuming 3 columns)
                    const columns = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
                    const currentRow = Math.floor(currentIndex / columns);

                    // Toggle all abstract details in the same row to match this one
                    for (let i = currentRow * columns; i < Math.min((currentRow + 1) * columns, allItems.length); i++) {
                        const rowItem = allItems[i];
                        const rowAbstractDetails = rowItem.querySelector('details.abstract-details');
                        if (rowAbstractDetails && rowAbstractDetails !== this) {
                            rowAbstractDetails.open = this.open;
                        }
                    }
                });
            });

            // Image modal functionality
            const paperImages = document.querySelectorAll('.paper-image');
            const modal = document.createElement('div');
            modal.className = 'image-modal';
            modal.innerHTML = '<span class="close-modal">&times;</span><img class="modal-content" alt="Paper preview enlarged">';
            document.body.appendChild(modal);

            const modalImg = modal.querySelector('.modal-content');
            const closeBtn = modal.querySelector('.close-modal');
            let currentImageIndex = -1;

            function showImage(index) {
                if (index >= 0 && index < paperImages.length) {
                    currentImageIndex = index;
                    const img = paperImages[index];
                    const fullsizeUrl = img.getAttribute('data-fullsize');
                    if (fullsizeUrl) {
                        // Hide the modal first to clear previous image
                        modal.classList.remove('show');
                        // Clear the previous image immediately
                        modalImg.src = '';
                        // Set new image and show modal
                        modalImg.src = fullsizeUrl;
                        modal.classList.add('show');
                    }
                }
            }

            paperImages.forEach((img, index) => {
                img.addEventListener('click', function() {
                    showImage(index);
                });
            });

            // Close modal when clicking the X or outside the image
            closeBtn.addEventListener('click', function() {
                modal.classList.remove('show');
                currentImageIndex = -1;
            });

            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    currentImageIndex = -1;
                }
            });

            // Close modal with Escape key and navigate with arrow keys
            document.addEventListener('keydown', function(e) {
                if (modal.classList.contains('show')) {
                    if (e.key === 'Escape') {
                        modal.classList.remove('show');
                        currentImageIndex = -1;
                    } else if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        if (currentImageIndex > 0) {
                            showImage(currentImageIndex - 1);
                        }
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        if (currentImageIndex < paperImages.length - 1) {
                            showImage(currentImageIndex + 1);
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>'''

    with open('index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate reading list HTML with paper thumbnails')
    parser.add_argument('--keep-pdfs', action='store_true',
                        help='Save downloaded PDFs to cache directory for offline reading')
    args = parser.parse_args()

    # Parse unread items from list.txt
    items = parse_list(keep_pdfs=args.keep_pdfs)

    # Generate HTML page
    generate_html(items)

    if args.keep_pdfs:
        print(f"PDFs saved to /tmp/arxiv_cache/")

    read = [item for item in items if item.read]
    unread = [item for item in items if not item.read]
    print(f"Generated page with {len(read)} read, and {len(unread)} unread.")
