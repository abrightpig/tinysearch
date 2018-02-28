from math import tanh
from sqlite3 import dbapi2 as sqlite

def dtanh(y):
    return 1.0 - y * y

class searchnet:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketables(self):
        self.con.execute('create table hiddennode(create_key)')
	self.con.execute('create table wordhidden(fromid, toid, strength)')
	self.con.execute('create table hiddenurl(fromid, toid, strength)')
	self.con.commit()

    def getstrength(self, fromid, toid, layer):
        if layer == 0: table = 'wordhidden'
	else: table = 'hiddenurl'
	res = self.con.execute('select strength from %s where fromid=%d and toid=%d' \
	                      %(table, fromid, toid)).fetchone()
	if res == None:
	    if layer == 0: return -0.2
	    if layer == 1: return 0
	return res[0]

    def setstrength(self, fromid, toid, layer, strength):
        if layer == 0: table = 'wordhidden'
	else: table = 'hiddenurl'
	res = self.con.execute('select rowid from %s where fromid=%d and toid=%d' % \
	                      (table, fromid, toid)).fetchone()
        if res == None:
	    self.con.execute('insert into %s (fromid, toid, strength) values (%d, %d, %f)' % \
	                     (table, fromid, toid, strength))
        else:
	    rowid = res[0]
	    self.con.execute('update %s set strength=%f where rowid=%d' % \
	                     (table, strength, rowid))

    def generate_hidden_node(self, wordids, urls):
        if len(wordids) > 3: return None
	#
	createkey = '_'.join(sorted([str(wi) for wi in wordids]))
	print "createkey:", createkey
	res = self.con.execute("select rowid from hiddennode where create_key='%s'" % createkey).fetchone()
        if res == None:
	    cur = self.con.execute("insert into hiddennode (create_key) values ('%s')" % createkey)
	    hiddenid = cur.lastrowid
	    # set default
	    for wordid in wordids:
	        self.setstrength(wordid, hiddenid, 0, 1.0 / len(wordids))
	    for urlid in urls:
	        self.setstrength(hiddenid, urlid, 1, 0.1)


    def get_all_hiddenids(self, wordids, urlids):
        ll = {}
	for wordid in wordids:
	    cur = self.con.execute('select toid from wordhidden where fromid=%d' % (wordid))
	    for row in cur: ll[row[0]] = 1
	for urlid in urlids:
	    cur = self.con.execute('select fromid from hiddenurl where toid=%d' % (urlid))
	    for row in cur: ll[row[0]] = 1
	return ll.keys()

    def print_net(self, info):
        print "*********************"
        print '[', info, ']'
        print "ai:", self.ai
        print "ah:", self.ah
        print "ao:", self.ao
        print "wi:", self.wi
        print "wo:", self.wo
        print 'show hiddennode:'
        for c in self.con.execute('select * from hiddennode'): print c
        print 'show wordhidden:'
        for c in self.con.execute('select * from wordhidden'): print c
        print 'show hiddenurl:'
        for c in self.con.execute('select * from hiddenurl'): print c

    def setup_network(self, wordids, urlids):
        # id list
	self.wordids = wordids  
	self.hiddenids = self.get_all_hiddenids(wordids, urlids)
	self.urlids = urlids

	# node output
	self.ai = [1.0] * len(self.wordids)
	self.ah = [1.0] * len(self.hiddenids)
	self.ao = [1.0] * len(self.urlids)

	# weight matrix 
	self.wi = [ [self.getstrength(wordid, hiddenid, 0) for hiddenid in self.hiddenids] 
	            for wordid in self.wordids]
	self.wo = [ [self.getstrength(hiddenid, urlid, 1) for urlid in self.urlids] 
	            for hiddenid in self.hiddenids]


    def feedforward(self):
        # init ai
	for i in range(len(self.wordids)):
	    self.ai[i] = 1.0
	
	# layer 0
	for j in range(len(self.hiddenids)):
	    sum = 0.0
	    for i in range(len(self.wordids)):
	        sum += self.ai[i] * self.wi[i][j]
	    self.ah[j] = tanh(sum)
	
	# layer 1
	for k in range(len(self.urlids)):
	    sum = 0.0
	    for j in range(len(self.hiddenids)):
	        sum += self.ah[j] * self.wo[j][k]
	    self.ao[k] = tanh(sum)
	
	return self.ao[:]

    def getresult(self, wordids, urlids): 
        self.setup_network(wordids, urlids)
        self.print_net("setup_networt")
	
	#return self.feedforward()
	result = self.feedforward()
	self.print_net("feedforward") 
	return result

    def back_propagate(self, targets, N=0.5):
        print '[back_propagate] ao:', self.ao
	print '[back_propagate] target:', targets
        # output error
	output_deltas = [0.0] * len(self.urlids)
	for k in range(len(self.urlids)):
	    error = targets[k] - self.ao[k]
	    output_deltas[k] = dtanh(self.ao[k]) * error

        # hidden error
	hidden_deltas = [0.0] * len(self.hiddenids)
	for j in range(len(self.hiddenids)):
	    error = 0.0
	    for k in range(len(self.urlids)):
	        error = error + output_deltas[k] * self.wo[j][k]
	    hidden_deltas[j] = dtanh(self.ah[j]) * error
	
	# update wo
	for j in range(len(self.hiddenids)):
	    for k in range(len(self.urlids)):
	        self.wo[j][k] += N * output_deltas[k] * self.ah[j]
	        #change = output_deltas[k] * self.ah[j]
		#self.wo[j][k] = self.wo[j][k] + N * change

        # update wi
	for i in range(len(self.wordids)):
	    for j in range(len(self.hiddenids)):
                self.wi[i][j] += N * hidden_deltas[j] * self.ai[i] 

    def train_query(self, wordids, urlids, selected_url):
        # generate hidden node
	self.generate_hidden_node(wordids, urlids)
        #self.print_net("generate_hidden_node")

	self.setup_network(wordids, urlids)
        self.print_net("setup_networt")

	self.feedforward()
        self.print_net("feedforward")
	
	targets = [0.0] * len(urlids)
	targets[urlids.index(selected_url)] = 1.0
	self.back_propagate(targets)
        self.print_net("back_propagate")

	self.update_database()
        self.print_net("update db")

    def update_database(self):
        # save database
	for i in range(len(self.wordids)):
	    for j in range(len(self.hiddenids)):
	        self.setstrength(self.wordids[i], self.hiddenids[j], 0, self.wi[i][j])
	for j in range(len(self.hiddenids)):
	    for k in range(len(self.urlids)):
	        self.setstrength(self.hiddenids[j], self.urlids[k], 1, self.wo[j][k])
	self.con.commit()
	


