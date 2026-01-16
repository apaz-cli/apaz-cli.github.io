#!/usr/bin/python3

import re
import os
import subprocess
import json
import base64
import hashlib
import tempfile
import shutil
from shlex import split
from os.path import splitext
from glob import glob
from sys import argv
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding

# Configuration
stylefile = "../resources/style/pandoc.html"
rss_description_max_length = 500
only = argv[1] if len(argv) > 1 else None

# Load password-protected articles
protected_articles = {}
try:
    with open(os.path.expanduser("~/git/Secrets/secrets/article_passwords.json")) as f:
        protected_articles = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

def run(cmd):
    subprocess.run(split(cmd), check=True)

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
    "A_History_of_Events_In_Case_You_Missed_Them",
  ]),
  ("Mirrored", [
    "rat",
    "bml",
    "khome",
    "shirt",
  ]),
]

def create_encrypted_html(original_html, password, title):
    """Create an encrypted HTML page with password prompt and decryption logic using AES-CBC with HMAC."""

    # Extract the body content to encrypt
    body_match = re.search(r'<body>(.*)</body>', original_html, re.DOTALL)
    if not body_match:
        return original_html  # Fallback if no body found

    body_content = body_match.group(1)

    # Load CryptoJS library
    cryptojs_path = os.path.join(os.path.dirname(__file__), 'crypto-js.min.js')
    with open(cryptojs_path) as f:
        cryptojs_code = f.read()

    # Extract all CSS from the original HTML's head section
    css_content = ""
    head_match = re.search(r'<head>(.*?)</head>', original_html, re.DOTALL)
    if head_match:
        # Extract all style tags and link tags
        head_content = head_match.group(1)
        css_content = '\n'.join(re.findall(r'<style[^>]*>.*?</style>', head_content, re.DOTALL))
    else:
        # Fallback to reading from pandoc.html
        with open(stylefile, "r") as css_file:
            css_content = css_file.read()

    # Encrypt the content using AES-CBC with HMAC
    # Derive from content hash so encryption is reproducible (no spurious git changes)
    content_hash = hashlib.sha256(body_content.encode('utf-8')).digest()

    # Derive deterministic salt from content hash
    salt = content_hash[:16]

    # Derive key from password using PBKDF2 (64 bytes: 32 for AES, 32 for HMAC)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=64,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    derived_key = kdf.derive(password.encode('utf-8'))
    encryption_key = derived_key[:32]  # First 32 bytes for AES
    hmac_key = derived_key[32:]  # Last 32 bytes for HMAC

    # Derive deterministic IV from content hash
    iv = content_hash[16:32]  # 16 bytes for AES IV

    # Pad and encrypt with AES-CBC
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(body_content.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Generate HMAC of ciphertext
    h = hmac.HMAC(hmac_key, hashes.SHA256(), backend=default_backend())
    h.update(ciphertext)
    auth_tag = h.finalize()

    # Base64 encode for embedding in HTML
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
    auth_tag_b64 = base64.b64encode(auth_tag).decode('utf-8')

    encrypted_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
{css_content}
    <style>
        .password-container {{
            max-width: 500px;
            margin: 100px auto;
            padding: 30px;
            text-align: center;
        }}
        .password-input {{
            padding: 10px;
            font-size: 16px;
            width: 250px;
            margin: 20px 0;
        }}
        .password-button {{
            padding: 10px 30px;
            font-size: 16px;
            cursor: pointer;
        }}
        .error-message {{
            color: red;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="password-container" id="password-prompt">
        <h2>This content is password protected</h2>
        <p>Please enter the password to view this page.</p>
        <input type="password" id="password-field" class="password-input" placeholder="Enter password">
        <br>
        <label style="font-size: 14px; margin: 10px 0; display: inline-block;">
            <input type="checkbox" id="show-password" onchange="togglePassword()"> Show password
        </label>
        <br>
        <button onclick="checkPassword()" class="password-button">Submit</button>
        <div id="error-msg" class="error-message"></div>
    </div>

    <script>
{cryptojs_code}
    </script>
    <script>
        const saltB64 = '{salt_b64}';
        const ivB64 = '{iv_b64}';
        const ciphertextB64 = '{ciphertext_b64}';
        const authTagB64 = '{auth_tag_b64}';

        function togglePassword() {{
            const passwordField = document.getElementById('password-field');
            const showPassword = document.getElementById('show-password');
            passwordField.type = showPassword.checked ? 'text' : 'password';
        }}

        function checkPassword() {{
            const passwordInput = document.getElementById('password-field').value;
            const errorMsg = document.getElementById('error-msg');

            // Show decrypting message
            errorMsg.textContent = 'Decrypting...';
            errorMsg.style.color = '#666';

            // Use setTimeout to let the UI update before the heavy computation
            setTimeout(() => {{
                try {{
                // Convert base64 to CryptoJS format
                const salt = CryptoJS.enc.Base64.parse(saltB64);
                const iv = CryptoJS.enc.Base64.parse(ivB64);
                const ciphertext = CryptoJS.enc.Base64.parse(ciphertextB64);
                const authTag = CryptoJS.enc.Base64.parse(authTagB64);

                // Derive key from password using PBKDF2 (64 bytes: 32 for AES, 32 for HMAC)
                const derivedKey = CryptoJS.PBKDF2(passwordInput, salt, {{
                    keySize: 512/32,  // 64 bytes = 512 bits
                    iterations: 100000,
                    hasher: CryptoJS.algo.SHA256
                }});

                // Split into encryption key and HMAC key
                const encryptionKey = CryptoJS.lib.WordArray.create(derivedKey.words.slice(0, 8));  // First 32 bytes
                const hmacKey = CryptoJS.lib.WordArray.create(derivedKey.words.slice(8, 16));  // Last 32 bytes

                // Verify HMAC
                const computedTag = CryptoJS.HmacSHA256(ciphertext, hmacKey);
                if (computedTag.toString() !== authTag.toString()) {{
                    throw new Error('Authentication failed');
                }}

                // Decrypt with AES-CBC
                const decrypted = CryptoJS.AES.decrypt(
                    {{ ciphertext: ciphertext }},
                    encryptionKey,
                    {{
                        iv: iv,
                        mode: CryptoJS.mode.CBC,
                        padding: CryptoJS.pad.Pkcs7
                    }}
                );

                // Convert to UTF-8 string
                const decryptedContent = decrypted.toString(CryptoJS.enc.Utf8);

                if (!decryptedContent) {{
                    throw new Error('Decryption produced empty result');
                }}

                    // Replace body content with decrypted content
                    document.body.innerHTML = decryptedContent;
                }} catch (e) {{
                    console.error('Decryption error:', e);
                    errorMsg.style.color = 'red';
                    errorMsg.textContent = 'Incorrect password';
                }}
            }}, 10);
        }}

        // Allow Enter key to submit
        document.getElementById('password-field').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                checkPassword();
            }}
        }});
    </script>
</body>
</html>'''

    return encrypted_html

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
        titlegroup = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        first_image = re.search(r'<img[^>]*src="([^"]*)"[^>]*>', html)

        meta_tags = ""
        if titlegroup:
            title_content = re.sub(r'\s+', ' ', titlegroup.group(1).strip())
            meta_tags += f"  <meta name=\"og:title\" content=\"{title_content}\">\n"

            description = get_description_from_html(filepath)
            if description:
                meta_tags += f"  <meta name=\"og:description\" content=\"{description}\">\n"

            if first_image:
                meta_tags += f"  <meta name=\"og:image\" content=\"{first_image.group(1)}\">\n"

        return html.replace("  <title>", meta_tags + "  <title>")

    # Extract just the filename without path or extension
    title = splitext(os.path.basename(f))[0]
    display_title = title.replace("_", " ")
    html_file = title + ".html"
    unstyled_file = title + "-unstyled.html"
    is_protected = title in protected_articles

    # Use temp directory for protected articles
    if is_protected:
        tmp_dir = tempfile.mkdtemp()
        styled_path = os.path.join(tmp_dir, title + ".html")
        unstyled_path = os.path.join(tmp_dir, title + "-unstyled.html")
    else:
        styled_path = html_file
        unstyled_path = unstyled_file

    # Generate HTML with pandoc
    run(f'pandoc -s --metadata pagetitle="{display_title}" -f markdown-smart -H {stylefile} {f} -o {styled_path}')
    run(f'pandoc -s --metadata pagetitle="{display_title}" -f markdown-smart {f} -o {unstyled_path}')

    # Process styled version
    with open(styled_path) as file:
        html = file.read()
        html = re.sub(replace, repwith, html, flags=re.DOTALL, count=1)
        html = replace_meta_with_opengraph(html, styled_path)

    if is_protected:
        html = create_encrypted_html(html, protected_articles[title], display_title)

    with open(html_file, "w") as file:
        file.write(html)

    # Process unstyled version
    with open(unstyled_path) as file:
        unstyled_html = re.sub("\s+<style>.*</style>", "", file.read(), flags=re.DOTALL, count=1)

    with open(unstyled_file, "w") as file:
        file.write(unstyled_html)

    if is_protected:
        shutil.rmtree(tmp_dir)

    return i, f

def gen_index():
    # Get all HTML files
    html_files = sorted([f for f in glob("*.html")
                         if not f.startswith("_") and f != "index.html" and not f.endswith("-unstyled.html")])

    # Filter out articles from secrets directory
    secrets_md_files = {splitext(os.path.basename(f))[0] for f in glob(os.path.expanduser("~/git/Secrets/secrets/blog/*.md"))}

    all_posts = [(f, get_title_from_html(f)) for f in html_files
                 if splitext(f)[0] not in secrets_md_files]

    # Build article to category mapping
    article_to_category = {article: cat_name
                          for cat_name, articles in categories
                          for article in articles}

    # Categorize posts
    categorized_posts = {cat_name: [] for cat_name, _ in categories}
    categorized_posts["Other"] = []

    for post_file, post_title in all_posts:
        basename = splitext(post_file)[0]
        category = article_to_category.get(basename, "Other")
        categorized_posts[category].append((post_file, post_title))

    # Build HTML
    with open(stylefile) as f:
        css = f.read()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Blog Index</title>
{css}
</head>
<body>
    <h1>Blog Posts</h1>
    <img src="images/100439997_p0.jpg" style="display: block; margin: 0 auto;" height=400>
"""

    # Output categories
    for cat_name, _ in categories:
        if categorized_posts[cat_name]:
            html += f"    <h2>{cat_name.upper()}</h2>\n    <ul>\n"
            for post_file, post_title in categorized_posts[cat_name]:
                html += f"        <li><a href=\"{post_file}\">{post_title}</a></li>\n"
            html += "    </ul>\n"

    if categorized_posts["Other"]:
        html += "    <h2>OTHER</h2>\n    <ul>\n"
        for post_file, post_title in categorized_posts["Other"]:
            html += f"        <li><a href=\"{post_file}\">{post_title}</a></li>\n"
        html += "    </ul>\n"

    html += "</body>\n</html>"

    with open("index.html", "w") as f:
        f.write(html)

def gen_rss():
    # Only include Programming and SFW articles
    allowed_articles = {article
                       for cat_name, articles in categories
                       if cat_name in {"Programming", "SFW"}
                       for article in articles}

    # Get all HTML files
    html_files = [f for f in glob("*.html")
                  if not f.startswith("_") and f != "index.html" and not f.endswith("-unstyled.html")]

    # Filter out articles from secrets directory
    secrets_md_files = {splitext(os.path.basename(f))[0] for f in glob(os.path.expanduser("~/git/Secrets/secrets/blog/*.md"))}

    rss_items = []
    for f in html_files:
        basename = splitext(f)[0]
        if basename not in allowed_articles or basename in secrets_md_files:
            continue

        title = get_title_from_html(f).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        description = get_description_from_html(f).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rss_items.append((f, title, description))

    # Build RSS feed
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

# Generate articles
# Glob from both local directory and secrets directory
local_md_files = [(i, f) for i, f in enumerate(glob("*.md"), 1) if not f.startswith("_")]
secrets_md_files = [(i, f) for i, f in enumerate(glob(os.path.expanduser("~/git/Secrets/secrets/blog/*.md")), len(local_md_files) + 1) if not os.path.basename(f).startswith("_")]

if only:
    local_md_files = [(i, f) for i, f in local_md_files if i == int(only)]
    secrets_md_files = [(i, f) for i, f in secrets_md_files if i == int(only)]

# Process both lists in parallel using the same executor
with ThreadPoolExecutor() as executor:
    # Process local files
    for i, f in executor.map(lambda args: generate_article(*args), local_md_files):
        print(f"Generated article {i}: {f}")

    # Process secrets files
    for i, f in executor.map(lambda args: generate_article(*args), secrets_md_files):
        print(f"Generated article {i}: {f}")

# Generate index and RSS
gen_index()
print("Generated index.html")

gen_rss()
print("Generated index.rss")
