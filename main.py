#!/usr/bin/env python
import os
import os.path as P
import requests
import lxml.html
import lxml.etree
import urlparse
import codecs
import datetime

import bs4

DEBUG = 0
HEADERS = ["categories: blog", "layout: post"]

class Entry:
    def __init__(self, title, text, updated, prev_entry_url):
        self.title = title
        self.text = text
        self.updated = updated
        self.prev_entry_url = prev_entry_url

    def save_to(self, destination_dir):
        opath = P.join(destination_dir, "%s %s.html" % (self.updated.strftime("%Y-%m-%d"), self.title))
        pretty_text = bs4.BeautifulSoup(self.text).prettify()
        lines = ["---", "title: %s" % self.title] + HEADERS + ["---", pretty_text]
        with codecs.open(opath, "w", "utf-8") as fout:
            fout.write("\n".join(lines))

    @staticmethod
    def download(url):
        """Download an entry from a URL and parse it."""
        r = requests.get(url)

        assert r.status_code == 200

        root = lxml.html.document_fromstring(r.text)

        prev_entry_url = None
        links = root.xpath("//span[@class='entry-linkbar-inner']/a/img[@alt='Previous Entry']")
        if links:
            prev_entry_url = links[0].getparent().get("href")
        if DEBUG:
            print prev_entry_url
        #assert prev_entry_url

        updated = None
        abbr = root.xpath("//abbr[@class='updated']")
        if abbr:
            # TODO: parse into datetime
            timestamp_str = abbr[0].get("title")
            # 2013-10-08T11:41:00+03:00
            # get rid of the UTC offset, since we can't parse it :(
            timestamp = datetime.datetime.strptime(timestamp_str[:-6], "%Y-%m-%dT%H:%M:%S")
            
        if DEBUG:
            print timestamp
        assert timestamp

        title = None
        dt = root.xpath("//dt[@class='entry-title']")
        if dt:
            title = dt[0].text
        if DEBUG:
            print title
        assert title

        entry_text = None
        dd = root.xpath("//div[@class='entry-content']")
        if dd:
            entry_text = lxml.etree.tostring(dd[0], pretty_print=True, encoding="utf-8")

        if DEBUG:
            print entry_text
        assert entry_text

        return Entry(title, entry_text, timestamp, prev_entry_url)

def create_parser():
    from optparse import OptionParser
    p = OptionParser("usage: %prog http://yourusername.livejournal.com/most-recent-entry.html")
    p.add_option("-d", "--debug", dest="debug", type="int", default="0", help="Set debugging level")
    p.add_option("", "--destination", dest="destination", type="string", default="html", help="Set destination directory")
    return p

def process_url(url, destination):
    """Download and save the specified URL.
    Returns the URL to the previous entry."""
    up = urlparse.urlparse(destination)
    _, fname = P.split(up.path)

    dest_path = P.join(destination, fname)

def main():
    global DEBUG
    p = create_parser()
    options, args = p.parse_args()
    DEBUG = options.debug

    if len(args) != 1:
        p.error("invalid number of arguments")

    if not P.isdir(options.destination):
        os.mkdir(options.destination)

    next_url = args[0]

    if not P.isdir(options.destination):
        os.mkdir(options.destination)

    while True:
        print next_url
        entry = Entry.download(next_url)
        entry.save_to(options.destination)
        next_url = entry.prev_entry_url
        if next_url is None:
            break

if __name__ == "__main__":
    main()
