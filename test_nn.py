import os
import nn

db_file = 'nn.db'
if os.path.exists(db_file):
    os.unlink(db_file)
    print 'delete db file:', db_file

mynet = nn.searchnet(db_file)
mynet.maketables()

w_world, w_river, w_bank = 101, 102, 103
u_worldbank, u_river, u_earth = 201, 202, 203

#mynet.generate_hidden_node([w_world, w_bank], [u_worldbank, u_river, u_earth])



#result = mynet.getresult([w_world, w_bank], [u_worldbank, u_river, u_earth])
#print "result:", result
#print 'show hiddennode:'
#for c in mynet.con.execute('select * from hiddennode'): print c
#print 'show wordhidden:'
#for c in mynet.con.execute('select * from wordhidden'): print c
#print 'show hiddenurl:'
#for c in mynet.con.execute('select * from hiddenurl'): print c

#mynet.train_query([w_world, w_bank], [u_worldbank, u_river, u_earth], u_worldbank)
#result = mynet.getresult([w_world, w_bank], [u_worldbank, u_river, u_earth])
#print "result:", result


all_urls = [u_worldbank, u_river, u_earth]
for i in range(20):
    mynet.train_query([w_world, w_bank], all_urls, u_worldbank)
    mynet.train_query([w_river, w_bank], all_urls, u_river)
    mynet.train_query([w_world], all_urls, u_earth)


#result = mynet.getresult([w_world, w_bank], all_urls)
#print "world bank, result:", result
#result = mynet.getresult([w_river, w_bank], all_urls)
#print "river bank, result:", result
result = mynet.getresult([w_bank], all_urls)
print "bank, result:", result
