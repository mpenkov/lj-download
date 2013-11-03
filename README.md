lj-download
===========

I wrote this script to help with migration from my LiveJournal blog to Jekyll.
Given the URL of the most recent entry in a journal, the script iteratively fetches entries until it gets to the oldest entry.
For each entry, it extracts the entry title, update time and actual entry content by using Xpath queries.
If LJ changes the page layout significantly in the future, then these queries may no longer work.

Pre-requisites
--------------

* requests - for downloading the HTML
* lxml - for parsing the HTML
* bs4 - for pretty-printing the HTML (I couldn't get lxml to do this for me)
* unidecode - for transliteration of the title (you don't need this if your blog is in English)

Running
-------

    ./main.py http://kogumamisha.livejournal.com/20145.html

This will download my Russian-language blog into the html subdirectory.
