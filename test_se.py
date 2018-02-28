import os
import searchengine

#pagelist = ['http://kiwitobes.com/wiki/Perl.html']

db_file = "searchindex.db"

# create table
#crawler = searchengine.crawler(db_file)
#crawler.createindextables()

pagelist = ['https://en.wikipedia.org/wiki/Python']
crawler = searchengine.crawler(db_file)

# crawl
#crawler.crawl(pagelist, depth=2)

# calculate pr
crawler.calculatepagerank(iterations=20)

# query
#se = searchengine.searcher('searchindex.db')
#se.getmatchrows('programming language')
#se.query('programming language')

