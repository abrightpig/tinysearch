import urllib2
import sys
from BeautifulSoup import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite

reload(sys)
sys.setdefaultencoding( "utf-8" )

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
        cur = self.con.execute("select rowid from %s where %s='%s'" % (table, field, value))
	res = cur.fetchone()
	if res == None:
	    cur = self.con.execute("insert into %s (%s) values ('%s')" % (table, field, value))
	    return cur.lastrowid
	else: 
	    # debug
	    #print "res: "
	    #print res
	    return res[0]

    # add index for page
    def addtoindex(self, url, soup):
        if self.isindexed(url): return
        print 'Indexing %s' % url

	# get word
	text = self.gettextonly(soup)
	#print("text: %s" % (text))
	words = self.seperatewords(text)
	print("words: %s" % (words))

	# get urlid
	urlid = self.getentryid('urllist', 'url', url)

	# link word to url
	for i in range(len(words)):
	    word = words[i]
	    if word in ignorewords: continue
	    #print("linking word:%s to url:%s" % (word, url))
	    wordid = self.getentryid('wordlist', 'word', word)
	    self.con.execute("insert into wordlocation(urlid, wordid, location) \
	                    values (%d, %d, %d)" % (urlid, wordid, i))

    # get text from page
    def gettextonly(self, soup):
        v = soup.string
	if v == None:
	    c = soup.contents
	    resulttext = ''
	    for t in c:
	        subtext = self.gettextonly(t)
		resulttext += subtext + '\n'
            return resulttext
	else:
	    return v.strip()

    # seperate words
    def seperatewords(self, text):
        #splitter = re.compile('"\\W*')
        splitter = re.compile('\W*')
	return [s.lower() for s in splitter.split(text) if s!='']

    # check if url already in index
    def isindexed(self, url):
        u = self.con.execute("select rowid from urllist where url='%s'" % (url)).fetchone()
	# debug 
	#print("u:")
	#print u
	if u!=None:
	    # check if already indexed
	    v = self.con.execute('select * from wordlocation where urlid=%d' % u[0]).fetchone()
	    if v!=None: return True
	return False


    # add url linking two pages
    def addlinkerref(self, urlFrom, urlTo, linkText):
        pass

    # crawl pages
    def crawl(self, pages, depth=2):
        for i in range(depth):
	    newpages = set()
	    count = 0 ###
	    for page in pages:
	        ### 
		#count = count + 1
		#if (count > 10):
		#    break
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
			print "linking %s %s" %(page, url) ###
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
     
        



