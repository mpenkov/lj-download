#!/usr/bin/env python
import os
import os.path as P
import requests
import lxml.html
import lxml.etree
import urlparse
import codecs
import datetime
import unidecode
import bs4
import urllib

DEBUG = 0

"""The headers to write for each post."""
HEADERS = ["categories: blog", "layout: post"]

def encode_title(title):
    """Jekyll posts are stored as individual files.
    It makes sense to name each file with the title of the post.
    However, Jekyll doesn't seem to handle file names with spaces or non-latin characters.
    It picks them up when building the site, but the actual links will be broken.
    This function encodes the title in such a way that it can be used as a filename for Jekyll posts."""
    #
    # You probably don't need the line below if your posts are in English
    #
    latin_title = unidecode.unidecode(title)
    encoded_title = urllib.quote_plus(latin_title.replace(" ", "-"))
    return encoded_title

def parse_previous_link(root):
    """Parse the link to the chronologically previous blog entry."""
    prev_entry_url = None
    links = root.xpath("//a[contains(@class,'b-controls-prev')]")
    if links:
        prev_entry_url = links[0].get("href")
    if DEBUG:
        print prev_entry_url
    return prev_entry_url

def parse_title(root):
    """Parse the title of a LiveJournal entry."""
    title = None
    dt = root.xpath("./head/meta[@property='og:title']/@content")
    if dt:
        title = dt[0]
    if DEBUG:
        print title
    assert title
    return title

def parse_timestamp(root):
    """Parse the timestamp of a LiveJournal entry.
    Returns a datetime.datetime instance."""
    published = root.xpath("//time[contains(@class,'published')]")
    if published:
        published_0 = published[0]
        t_year = int(published_0.xpath("./a")[0].text)
        t_month = int(published_0.xpath("./a")[1].text)
        t_day = int(published_0.xpath("./a")[2].text)
        #TODO: parse time
        timestamp = datetime.datetime(t_year, t_month, t_day)        
    if DEBUG:
        print timestamp
    assert timestamp
    return timestamp

def parse_entry_text(root):
    """Parse the actual entry text of a LiveJournal entry.
    Returns a UTF-8 encoded byte string."""
    #
    # Here we only grab the HTML fragment that corresponds to the entry context.
    # Throw everything else away.
    #
    entry_text = None
    dd = root.xpath("//div[@class='b-singlepost-bodywrapper']")
    if dd:
        entry_text = lxml.etree.tostring(dd[0], pretty_print=True, encoding="utf-8")
    if DEBUG:
        print entry_text
    assert entry_text
    return entry_text

def parse_tags(root):
    """Returns the tags for a LiveJournalEntry."""
    tags = []
    a = root.xpath("./head/meta[@property='article:tag']/@content")
    if a:
        tags = [aa for aa in a]
    if DEBUG:
        print tags
    return tags

class Entry:
    """Represents a single LiveJournal entry.
    Includes functions for downloading an entry from a known URL."""
    def __init__(self, title, text, updated, prev_entry_url, tags):
        self.title = title
        self.text = text
        self.updated = updated
        self.prev_entry_url = prev_entry_url
        self.tags = tags

    def save_to(self, destination_dir, overwrite=False):
        """Save the entry to the specified directory.
        The filename of the entry will be determined from its title and update time.
        The entry will contain a Jekyll header with a HTML fragment representing the content."""
        title = encode_title(self.title)
        opath = P.join(destination_dir, "%s-%s.html" % (self.updated.strftime("%Y-%m-%d"), title))
        #
        # self.text is currently a UTF-8 encoded string, but prettify turns it into a Unicode string.
        #
        pretty_text = bs4.BeautifulSoup(self.text, "lxml").prettify()
        lines = ["---", "title: %s" % self.title] + HEADERS + ["tags: " + " ".join(self.tags), "---", pretty_text]
        #
        # TODO:
        # If the filenames aren't unique enough (e.g. same date, same title), the entries may end up overwriting each other.
        #
        if not overwrite:
            assert not P.isfile(opath)
        with codecs.open(opath, "w", "utf-8") as fout:
            fout.write("\n".join(lines))

    @staticmethod
    def download(url):
        """Download an entry from a URL and parse it."""
        r = requests.get(url)
        assert r.status_code == 200

        root = lxml.html.document_fromstring(r.text)
        title = parse_title(root)
        tags = parse_tags(root)
        entry_text = parse_entry_text(root)
        timestamp = parse_timestamp(root)
        prev_entry_url = parse_previous_link(root)

        return Entry(title, entry_text, timestamp, prev_entry_url, tags)

def create_parser():
    from optparse import OptionParser
    p = OptionParser("usage: %prog http://yourusername.livejournal.com/most-recent-entry.html")
    p.add_option("-d", "--debug", dest="debug", type="int", default="0", help="Set debugging level")
    p.add_option("", "--destination", dest="destination", type="string", default="html", help="Set destination directory")
    p.add_option("-f", "--force-overwrite", dest="overwrite", action="store_true", default=False, help="Overwrite existing files")
    return p

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

    while next_url is not None:
        print next_url
        entry = Entry.download(next_url)
        entry.save_to(options.destination, overwrite=options.overwrite)
        next_url = entry.prev_entry_url

if __name__ == "__main__":
    main()
