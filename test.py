import searchengine

#pagelist = ['http://kiwitobes.com/wiki/Perl.html']
pagelist = ['https://en.wikipedia.org/wiki/Python']
crawler = searchengine.crawler('searchindex.db')

crawler.createindextables()

#crawler.crawl(pagelist)

