#!/usr/bin/python3

import os
import sys
import shutil
import subprocess
from shlex import split
from os import chdir as cd
from glob import glob

css = """<style type="text/css">
/* https://github.com/markdowncss/retro/blob/master/css/retro.css */

@font-face {
    font-family: "lemon";
    src: url('lemon.woff');
}

/*
@media print {
    *, *:before, *:after {
        background: transparent !important;
        color: #000 !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }
    a, a:visited { text-decoration: underline; }
    a[href]:after { content: " (" attr(href) ")"; }
    abbr[title]:after { content: " (" attr(title) ")"; }
    a[href^="#"]:after, a[href^="javascript:"]:after { content: ""; }
    pre, blockquote { border: 1px solid #999; page-break-inside: avoid; }
    thead { display: table-header-group; }
    tr, img { page-break-inside: avoid; }
    img { max-width: 100% !important; }
    p, h2, h3 { orphans: 3; widows: 3; }
    h2, h3 { page-break-after: avoid; }
}
*/
a, a:visited { color: #01ff70; }
a:hover, a:focus, a:active { color: #2ecc40; }
.retro-no-decoration { text-decoration: none; }
p, .retro-p {
    font-size: 1rem;
    margin-bottom: 1.3rem;
    /*text-indent: 50px*/
}
h1, .retro-h1, h2, .retro-h2, h3, .retro-h3, h4, .retro-h4 {
    margin: 1.414rem 0 .5rem;
    font-weight: inherit;
    line-height: 1.42;
}
h1, .retro-h1 {
    color: rgb(112, 221, 0);
    margin-top: 0;
    font-size: 3.998rem;
}
h2, .retro-h2 {
    color: rgb(112, 221, 0);
    margin-top: 0;
    font-size: 2.827rem;
}
h3, .retro-h3 {
    font-size: 1.999rem;
}
h4, .retro-h4 {
    font-size: 1.414rem;
}
h5, .retro-h5 {
    font-size: 1.121rem;
}
h6, .retro-h6 {
    font-size: .88rem;
}
small, .retro-small {
    font-size: .707em;
}

img, canvas, iframe, video, svg, select, textarea { max-width: 100%; }

html, body {
    /* background-image: url(https://raw.githubusercontent.com/apaz-cli/apaz-cli.github.io/master/pattern.png); */
    background-color: #222;
    min-height: 100%;
    font-size: 20px;
}
body {
    color: #fafafa;
    font-family: "lemon", "Courier New";
    line-height: 1.65;
    margin: 6rem auto 1rem;
    max-width: 48rem;
    /* padding: .25rem; */
}
pre, code {
    background-color: #333;
    font-family: "lemon", "Menlo", "Monaco", "Courier New";
    font-size: 12;
}

code span.dt { color: #e4a51e; } /* DataType */

pre {
    padding: .5rem;
    line-height: 1.25;
    overflow-x: scroll;
}
blockquote {
    border-left: 3px solid #01ff70;
    padding-left: 1rem;
}
</style>
"""

with open("pandoc.css", "w") as f:
    f.write(css)


run = lambda s: subprocess.run(split(s), check=True)

for f in glob('*.md'):
    un="_";sp=" "

    title = os.path.splitext(f)[0]
    to = title + '.html'

    run(f'pandoc --metadata pagetitle="{title.replace(un, sp)}" -f markdown-smart -H pandoc.css {f} -o {to}')

os.remove('pandoc.css')
