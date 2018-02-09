import os
import searchengine

#pagelist = ['http://kiwitobes.com/wiki/Perl.html']

db_file = "searchindex.db"


pagelist = ['https://en.wikipedia.org/wiki/Python']
crawler = searchengine.crawler(db_file)
if not os.path.exists(db_file):
    #os.remove(db_file)
    #os.unlink(my_file)
    crawler.createindextables()
crawler.crawl(pagelist)

