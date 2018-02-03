import urllib2
from BeautifulSoup import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite

# ignore words
ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class crawler:
    # init crawler
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)
    
    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    # get entry id, add to db if not exsited
    def getentryid(self, table, field, value, createnew = True):
        return None

    # add index for page
    def addtoindex(self, url, soup):
        print 'Indexing %s' % url

    # get text from page
    def gettextonly(self, soup):
        return None

    # seperate words
    def seperatewords(self, text):
        return None

    # check if url already in index
    def isindexed(self, url):
        return False

    # add url linking two pages
    def addlinkerref(self, urlFrom, urlTo, linkText):
        pass

    # crawl pages
    #def crawl(self, pages, depth=2):
    def crawl(self, pages, depth=1):
        for i in range(depth):
	    newpages = set()
	    count = 0 ###
	    for page in pages:
	        ### 
		count = count + 1
		if (count > 10):
		    break
		###
	        try:
		    # page: url
		    c = urllib2.urlopen(page)
		except:
		    print "could not open %s" % (page)
		    continue
		soup = BeautifulSoup(c.read())
		# url -> content
		self.addtoindex(page, soup)

                # e.g: 
		# <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
		# <a href="http://example.com/lacie" class="sister" id="xiaodeng">Lacie</a>
		links = soup('a')
		for link in links:
		    if ('href' in dict(link.attrs)):
		        # join domain & uri
		        url=urljoin(page, link['href'])
			if url.find("'") != -1: continue # ??
			#print "page=%s link=%s url=%s" %(page, link, url) ###
			url = url.split('#')[0]
			if url[0:4] == 'http' and not self.isindexed(url):
			    newpages.add(url)
			linkText = self.gettextonly(link)
			#print linkText
			self.addlinkerref(page, url, linkText)
	            
		self.dbcommit()
            pages=newpages

    # create db
    def createindextables(self):
        self.con.execute("create table urllist(url)")
        self.con.execute("create index urlidx on urllist(url)")

        self.con.execute("create table wordlist(word)")
        self.con.execute("create index wordinx on wordlist(word)")
        
	self.con.execute("create table wordlocation(urlid, wordid, location)")
        self.con.execute("create index wordurlidx on wordlocation(wordid)")
        
	self.con.execute("create table link(fromid integer, toid integer)")
	self.con.execute("create index urltoidx on link(toid)")
	self.con.execute("create index urlfromidx on link(fromid)")

        self.con.execute("create table linkwords(wordid, linkid)")
	self.dbcommit()
     
        





