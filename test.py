import os
import searchengine

#pagelist = ['http://kiwitobes.com/wiki/Perl.html']

db_file = "searchindex.db"

# create table
#crawler = searchengine.crawler(db_file)
#crawler.createindextables()

# crawl
pagelist = ['https://en.wikipedia.org/wiki/Python']
#crawler = searchengine.crawler(db_file)
#crawler.crawl(pagelist, depth=2)

# search
se = searchengine.searcher('searchindex.db')
se.getmatchrows('programming language')
