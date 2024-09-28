#!/usr/bin/python3

import re
import os
"""
The variables that you are meant to change are those that are defined in the first block here before the function definitions.
Note that this is just plaintext that gets inserted into the string below. It's not elegant, but it works.
That also means that you can somewhat style some of these strings by entering them with valid HTML syntax should you want to do so.
"""
TitleText = 'apaz\'s Website'
TabTitle = TitleText
SubText = 'Articles:'
importPath = 'content.txt'
outputPath = "index.html"
hourOffset = 0


def parseContents():
    contents = None
    with open(importPath, "r") as file:
        contents = file.read()

    while contents[0] == '\n':
        contents = contents[1:]
    while contents[-1] == '\n':
        contents = contents[:-1]
    contents = re.sub('\n{3,}', '\n\n', contents)
    contents = contents.split('\n\n')
    return [x.split('\n') for x in contents]


def makeDoc(data):
    with open(outputPath, 'w') as file:
        page = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="author" content="apaz">
    <meta name="viewport" content="width=device-width,initial-scale=1">

    <meta name="og:title" content="apaz's Website">
    <meta name="og:description" content="My blog and projects.">
    <meta name="og:image" content="https://apaz-cli.github.io/resources/images/sip.png">

    <title>apaz's Website</title>
    <link rel="stylesheet" href="main.css">
    <link rel="icon" type="image/png" href="resources/images/favicon.png">

    <link rel="preload"  href="resources/images/1.jpg">
    <link rel="prefetch" href="resources/images/2.jpg">
    <link rel="prefetch" href="resources/images/3.jpg">
    <link rel="prefetch" href="resources/images/4.jpg">
    <link rel="prefetch" href="resources/images/5.jpg">
    <link rel="prefetch" href="resources/images/6.jpg">
</head>
<body>
    <div class="bg-image"></div>
    <div class="window-bg">
        <div class="front-img"></div>
        <div class="titlediv">
            <div id=titleb>'''+TitleText+'''</div>
            <div id="clock"></div>
        </div>
        <div class="windowbackgroundarea1"><div id="Subtitle">'''+SubText+'''</div></div>
        <div class="windowbackgroundarea2">
        <div class="centerDivs">
            <div class="category">
'''
        # Write out the content, combining short lines.
        for i, category in enumerate(data):
            page += ('\n' if i else '') + \
                    '                <div class="categorytitle">' + \
                    category[0] + '</div>\n'
            page += '                <div class="categorycontent">'
            linelength = 0
            for entry in category[1:]:
                name, link = entry.split(' | ')
                name = name.strip()
                link = link.strip()
                linelength += len(name)+3
                if linelength > 50:
                    page = page[:-3]+'</div>\n                <div class="categorycontent">'
                    page += '<a href="'+link+'">'+name+'</a> - '
                    linelength = len(name)
                else:
                    page += '<a href="'+link+'">'+name+'</a> - '
            if page[-3:] == ' - ':
                page = page[:-3]+'</div>\n'
            else:
                page += '</div>\n'
        page += '''            </div>
        </div>
        </div>
    </div>
    <div class="pixeloverlay"></div>
    <div class="vignette"></div>
    <script>
        var clock=document.getElementById("clock");
        function updateClock(){
            var date=new Date();
            date.setHours(date.getHours()+'''+str(hourOffset)+''')
            var hours = date.getHours().toString();
            var minutes = date.getMinutes().toString();
            var seconds = date.getSeconds().toString();
            if (hours.length==1){
                hours="0"+hours
            }
            if (minutes.length==1){
                minutes="0"+minutes
            }
            if (seconds.length==1){
                seconds="0"+seconds
            }
            clock.innerHTML=hours+":"+minutes+":"+seconds;
        }
        updateClock();
        setInterval(updateClock,1000);
    </script>
    </body>
    </html>'''
        file.write(page)


def makeBlog():
    os.chdir('blog/')
    os.system('./generate.py')


if __name__ == "__main__":
    contents = parseContents()
    print('Parsed content file.')
    makeDoc(contents)
    print('Created main HTML page.')
    makeBlog()
    print('Done.')
