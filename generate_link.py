#!/usr/bin/python
import os
from collections import defaultdict
from BeautifulSoup import BeautifulSoup
import urllib2
import re

import jinja2
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

def download(url, directory, fname):
    if not os.path.exists(directory):
        os.makedirs(directory)
    fullpath="./"+directory+"/"+fname
    if not os.path.isfile(fullpath):
        print "downloading from "+url+" to "+ fullpath 
        resp = urllib2.urlopen(url)
        fh = open(fullpath, "w")
        fh.write(resp.read())
        fh.close()

data = {}
# 1. get all pdf files from the page
html_page = urllib2.urlopen("http://botanicalgarden.berkeley.edu/springplantsale")
soup = BeautifulSoup(html_page)
for div in soup.findAll('div', { "class" : "pane" }):
    ftype=''
    sub = div.get('id')
    if 'plant' in sub:
        ftype='plants'
    elif 'map' in sub:
        ftype='maps'
    if ftype:
        data[ftype]={}
        for link in div.findAll('a'):
            url = link.get('href')
            fname = url[url.rfind("/")+1:]
            catagory = fname[:fname.rfind("-")]
            download(url, ftype, fname)
            if 'plants' == ftype:
                plantlist=[]
                title = ""
                fulltxt = convert_pdf_to_txt(ftype+"/"+fname)
                for line in fulltxt.splitlines():
                    cleanup = "".join([ch for ch in line.strip() if ch.isalnum() or ch.isspace()])
                    cleanup = re.sub(' +', ' ', cleanup)
                    if '2018' in cleanup:
                        title = line
                    elif len(cleanup):
                        detail = {'name':cleanup, 'keyword':re.sub(' +', '+', cleanup)}
                        plantlist.append(detail)
                data[ftype][catagory] = {"file":fname, "title": title, "list":plantlist}

template = """ 
    <html>
        <body>
        {% for cat, value in plants.iteritems() %}
        <h2>{{ value.title }}</h2>
        <ul>
            {% for detail in value.list %}
            <li><a href="https://www.google.com/search?q={{ detail.keyword }}&source=lnms&tbm=isch" target="_blank">{{ detail.name }}</a></li>
            {% endfor %}
        </ul>
        {% endfor %}
        </body>
        </html>"""
temp = jinja2.Template(template)

pagefile = open('plants.html', 'w+')
pagefile.write(temp.render(data))
pagefile.close()
