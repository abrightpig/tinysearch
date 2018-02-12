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
        splitter = re.compile('\\W*')
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
	        ## 
		#count = count + 1
		#if (count > 10):
		#    break
		##
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
        print("creating table urllist...")
        self.con.execute("create table urllist(url)")
        self.con.execute("create index urlidx on urllist(url)")

        print("creating table wordlist...")
        self.con.execute("create table wordlist(word)")
        self.con.execute("create index wordinx on wordlist(word)")
        
        print("creating table wordlocation...")
	self.con.execute("create table wordlocation(urlid, wordid, location)")
        self.con.execute("create index wordurlidx on wordlocation(wordid)")
        
        print("creating table link...")
	self.con.execute("create table link(fromid integer, toid integer)")
	self.con.execute("create index urltoidx on link(toid)")
	self.con.execute("create index urlfromidx on link(fromid)")

        print("creating table linkwords...")
        self.con.execute("create table linkwords(wordid, linkid)")
	self.dbcommit()
     
        


class searcher:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def getmatchrows(self, q):
        # generate query string
	fieldlist = 'w0.urlid'
	tablelist = ''
	clauselist = ''
	wordids = []

	# prepare query
	words = q.split(' ')
	tablenum = 0
	for word in words:
	    # get word id
	    wordrow = self.con.execute("select rowid from wordlist where word='%s'" % (word)).fetchone()
            if wordrow != None:
	        wordid = wordrow[0]
		wordids.append(wordid)
		if tablenum > 0:
		    tablelist += ','
		    clauselist += ' and '
		    clauselist += ' w%d.urlid=w%d.urlid and ' % (tablenum - 1, tablenum)
		fieldlist += ',w%d.location' % tablenum
		tablelist += 'wordlocation w%d' % tablenum
		clauselist += 'w%d.wordid=%d' % (tablenum, wordid)
		tablenum += 1
	
	# execute query
	fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        print fullquery 
	cur = self.con.execute(fullquery)
	rows = [row for row in cur]

        #print 'rows:'
	#print rows
        #print 'wordid:'
	#print wordids
	return rows, wordids
       
    def getscoredlist(self, rows, wordids):
        totalscores = dict([(row[0], 0) for row in rows])

	# todo 
	#weights = [(1.0, self.frequencyscore(rows))]
	#weights = [(1.0, self.locationscore(rows))]
	#weights = [(1.0, self.distancescore(rows))]
	weights = [(1.0, self.locationscore(rows)),(1.5, self.frequencyscore(rows)),(1.5, self.distancescore(rows))]

	for (weight, scores) in weights:
	    ## print "weight", weight
	    for url in totalscores:
	        totalscores[url] += weight * scores[url]
	        ## print "weight", weight, "url", url,  "totalscores[url]", totalscores[url]
	return totalscores

    def geturlname(self, id):
        return self.con.execute("select url from urllist where rowid=%d" % (id)).fetchone()[0]

    def query(self, q):
        rows, wordids = self.getmatchrows(q)
	scores = self.getscoredlist(rows, wordids)
	print "scores", scores
        rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
	for (score, urlid) in rankedscores[0:10]:
	    print '%f \t %s' % (score, self.geturlname(urlid))

    ## to analyze
    def normalizescores(self, scores, smallIsBetter = 0):
        vsmall = 0.00001           # very small constant
	if smallIsBetter:
	    minscore = min(scores.values())
	    return dict([(u, float(minscore)/max(vsmall,l)) for (u,l) in scores.items()])
	else:
	    maxscore = max(scores.values())
	    if maxscore == 0: maxscore = vsmall
	    return dict([(u, float(c) / maxscore) for (u,c) in scores.items()])

    # score_1: frequency
    def frequencyscore(self, rows):
        counts = dict([(row[0],0) for row in rows])
	for row in rows: counts[row[0]] += 1
	return self.normalizescores(counts)

    # score_2: location
    def locationscore(self, rows):
        locations = dict([(row[0], 1000000) for row in rows])
	for row in rows:
	    loc = sum(row[1:])
	    #print  "row:", row, "row[1:]", row[1:], "locations", locations[row[0]], "loc:", loc
	    if loc < locations[row[0]]: locations[row[0]] = loc
	return self.normalizescores(locations, smallIsBetter = 1)

    # score_3: distance
    def distancescore(self, rows):
        # equivalent score for only one word  
	if len(rows[0]) <= 2: return dict([row[0], 1.0] for row in rows)

        mindistance = dict([(row[0], 1000000) for row in rows])

	for row in rows:
	    dist = sum([abs(row[i] - row[i-1]) for i in range(2,len(row))])
	    if dist < mindistance[row[0]]: mindistance[row[0]] = dist
	return self.normalizescores(mindistance, smallIsBetter=1)
