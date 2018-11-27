import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, abort,flash

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

DB_USER = "hz2562"
DB_PASSWORD = "dp99rrq9"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

#engine.execute("""DROP TABLE IF EXISTS test;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS test ( id serial, name text UNIQUE );""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

engine.execute("""DROP TABLE IF EXISTS testUser;""")
engine.execute("""CREATE TABLE IF NOT EXISTS testUser ( uid serial, name text UNIQUE, password text );""")
engine.execute("""INSERT INTO testUser(name,password) VALUES ('user','pass');""")
engine.execute("""DELETE FROM Wine WHERE grapetype = 'testGrape';""")
engine.execute("""DELETE FROM Location WHERE winery = 'testWinery';""")


@app.before_request
def before_request():
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	try:
		g.conn.close()
	except Exception as e:
		pass

@app.route('/')
def index():
	print(request.args)

	cursor = g.conn.execute("WITH PopWine(wid) AS (SELECT wid \
	FROM UserWishWine WW WHERE wid IN \
		(SELECT wid \
		FROM Review U \
		GROUP BY wid \
		HAVING AVG(U.point) > 80) \
	GROUP BY wid \
	ORDER BY COUNT(uid) DESC \
	LIMIT 10) \
	SELECT winery, grapeType\
	FROM (PopWine P JOIN Wine W ON P.wid = W.wid) AS PW JOIN Location L \
	ON PW.lid = L.lid;")
	names = []
	for result in cursor:
		names.append('Winery: %s , Grape: %s'%(result['winery'],result['grapetype']))  # can also be accessed using result[0]
	cursor.close()

	context = dict(data = names)
	return render_template("index.html", **context)

@app.route('/signup', methods = ['GET','POST']) # FINISHED
def signup():
	if request.method == 'POST':
		uid = request.form['uid']
		name = request.form['name']
		psw = request.form['psw']
		try:
			g.conn.execute('INSERT INTO webUser(uid,name,password) VALUES (\'%s\',\'%s\',\'%s\')'% (uid,name,psw));
			return redirect('/')
		except:
			flash("User ID already exist")
			return redirect('/signup')

	return render_template("signup.html") 

@app.route('/login', methods = ['GET','POST']) # FINISHED
def login():
	if request.method == 'POST':
		uid = request.form['uid']
		psw = request.form['psw']
		try: 
			userid = g.conn.execute('SELECT uid FROM webUser WHERE uid=\'%s\' AND password = \'%s\''%(uid, psw))
			uidL = []
			for result in userid:
				print(result)
				uidL.append(result['uid'])
			userid.close()
			if not uidL:
				raise sqlalchemy.exc.IntegrityError
			session['currUser'] = uid
			return redirect('/user/%s'%uid)
		except:
			flash('Invalid User ID or Password')
			return redirect('/login')

	return render_template("login.html")  

@app.route('/user/<uid>')
def user(uid):
	if 'currUser' not in session:
		return redirect('/login')

	username = g.conn.execute('SELECT name FROM webUser WHERE uid = \'%s\''%(uid))
	name = []
	for user in username:
		name.append(user['name'])
	username.close()

	wished = g.conn.execute('SELECT * FROM UserWishWine WHERE uid = \'%s\''%(uid))
	wine = []
	for item in wished:
		wine.append(item['wid'])
	wished.close()
	if not wine:
		wine.append("Oops, you haven't wished any wine yet.")
	context = dict(data = wine)

	return render_template("user.html", name=name[0], **context)

@app.route('/logout') # FINISHED
def logout():
	session.pop('currUser')
	return redirect('/') 

@app.route('/wineInfo/<wineid>') 
def wineInfo(wineid, methods=['POST']):

	query = "WITH onlyWine AS (SELECT * FROM wine WHERE wid = " + wineid + ") "
	query = query + "SELECT * FROM onlyWine AS o JOIN Location AS l ON l.lid = o.lid"

	#print(query)


	# execute the query
	valid_wine = g.conn.execute(query)
	wine = []
	for item in valid_wine:
		wineInfoString = 'Wine # %s:\n'%(item['wid'])
		wine.append(wineInfoString)

		wineInfoString = "Grape Type: "+ item['grapetype'] + "\n"
		wine.append(wineInfoString)

		# country
		if item['country'] is not None:
			wineInfoString = "Country: " + item['country'] + "\n"
		else:
			wineInfoString = "Country: -\n"
		wine.append(wineInfoString)

		# province
		if item['province'] is not None:
			wineInfoString ="Province: " + item['province'] + "\n"
		else:
			wineInfoString ="Province: -\n"
		wine.append(wineInfoString)

		# region1
		if item['region1'] is not None:
			wineInfoString =  "Sub-region1: " + item['region1'] + "\n"
		else:
			wineInfoString =  "Sub-region1: -\n"
		wine.append(wineInfoString)

		# region2
		if item['region2'] is not None:
			wineInfoString = "Sub-region2: " + item['region2'] + "\n"
		else:
			wineInfoString = "Sub-region2: -\n"
		wine.append(wineInfoString)

		# winery
		if item['winery'] is not None:
			wineInfoString = "Winery: " + item['winery'] + "\n"
		else:
			wineInfoString = "Winery: -\n"
		wine.append(wineInfoString)

		# vinyard
		if item['vinyard'] is not None:
			wineInfoString = "Vinyard: " + item['vinyard'] + "\n"
		else:
			wineInfoString = "Vinyard: -\n"
		wine.append(wineInfoString)

	valid_wine.close()

	# get average point
	query = 'SELECT AVG(point) AS  avg FROM Review WHERE wid = ' + wineid + ';'
	avg_point = g.conn.execute(query)
	for item in avg_point:
		wineInfoString = 'Average Rating: ' + str(round(item['avg'],2))
		wine.append(wineInfoString)
	avg_point.close()
	num2wine = len(wine)

	# get the tags
	query = 'WITH wineTag AS(SELECT uid, content FROM UserLikeTag WHERE wid = ' + wineid + ')'
	query = query + 'SELECT content FROM wineTag GROUP BY content ORDER BY COUNT(*) DESC;'
	tags = g.conn.execute(query)
	for item in tags:
		wineInfoString = str(item['content'])
		wine.append(wineInfoString)
	tags.close()
	num2tag = len(wine)

	# getting the review
	query = 'WITH validReview AS (SELECT rid, uid, title, description, point FROM Review WHERE wid = ' + wineid + ')'
	query = query + 'SELECT u.name, r.title, r.description, r.rid, r.point FROM validReview AS r JOIN WebUser AS u ON r.uid = u.uid'
	query = query + ' ORDER BY point DESC'
	review_list = g.conn.execute(query)
	index = 1
	for item in review_list:
		wineInfoString = '#' + str(index) + ': '
		wineInfoString = wineInfoString + 'Reviewer: ' + item['name'] + '     '
		wineInfoString = wineInfoString + 'Point: ' + str(item['point']) + '/100'
		wine.append(wineInfoString)
		wineInfoString = "Description: " + item['description']
		wine.append(wineInfoString)
		wineInfoString = "-"
		wine.append(wineInfoString)
		index = index + 1
	review_list.close()

	context = dict(data = wine)

	logedIn = ''
	uTag = []

	if 'currUser' in session:
		logedIn = session['currUser']
		try:
			liked = g.conn.execute('SELECT content FROM UserLikeTag WHERE uid = \'%s\' AND wid = \'%s\''%(logedIn,wineid))
			for item in liked:
				uTag.append(wine.index(item['content']))
			liked.close()
			#idx = dict(dataT = uTag)
		except:
			print("no liked tags")
	idx = dict(dataT = uTag)

	return render_template("wineInfo.html", num2wine=num2wine, datalen=len(wine), num2tag=num2tag, **context, wid = wineid, log=logedIn, **idx)

@app.route('/search' , methods = ['GET','POST']) #FINISHED
def search():
	if request.method == 'POST':
		info = {}
		grapetype = request.form['grape_type']
		info['winery'] = request.form['winery']
		info['country'] = request.form['country']
		info['province'] = request.form['province']
		info['region1'] = request.form['region1']
		info['region2'] = request.form['region2']
		info['vinyard'] = request.form['vinyard']

		locQuery = "WHERE"
		for key, val in info.items():
			if val != '':
				locQuery = locQuery + ' %s ~* \'%s\' AND'%(key,val)

		locQuery = locQuery[0:len(locQuery)-4]

		query = 'WITH loc AS ( SELECT lid, country FROM Location %s )\
				SELECT w.grapetype, w.wid, l.country \
				FROM wine AS w \
				JOIN loc AS l ON w.lid = l.lid'%(locQuery)
		#print(query)

		if grapetype != '':
			query = query + " WHERE w.grapeType ~* \'" + grapetype + "\'"

		query = query + " ORDER BY w.wid ASC"

		#print("\n" + query + "\n")

		# execute the query
		valid_wine = g.conn.execute(query)
		wine = []
		for item in valid_wine:
			wineInfoString = 'Wine # %s'%(item['wid'])
			wineInfoString = wineInfoString + ' : ' + item['grapetype'] + " Wine"
			if item['country'] is not None:
				wineInfoString = wineInfoString + ", from " + item['country']
			wine.append(wineInfoString)

		valid_wine.close()
		context = dict(data = wine)

		if len(wine) != 0:
			return render_template("searchResult.html", **context)
		else:
			return render_template("noWine.html")


	return render_template("search.html")

@app.route('/noWine') #FINISHED
def noWine():
	logedIn = ''
	if 'currUser' in session:
		logedIn = session['currUser']
	return render_template("noWine.html", log = logedIn)

@app.route('/addWine', methods = ['GET','POST']) # FINISHED
def addWine():
	if request.method == 'POST':
		grapetype = request.form['grape_type']
		winery = request.form['winery']
		country = request.form['country']
		province = request.form['province']
		region1 = request.form['region1']
		region2 = request.form['region2']
		vinyard = request.form['vinyard']

		try:
			try:
				addLoc = g.conn.execute('INSERT INTO Location(winery,country,province,region1,region2,vinyard) VALUES (\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')' \
				% (winery,country,province,region1,region2,vinyard));
				addLoc.close()
			except sqlalchemy.exc.IntegrityError:
				pass
			
			query = 'WHERE winery = \'%s\' AND country = \'%s\' AND province = \'%s\' AND region1 = \'%s\' AND region2 = \'%s\' AND vinyard = \'%s\'' \
			%(winery,country,province,region1,region2,vinyard)
			getId = g.conn.execute('SELECT lid FROM Location %s'%(query))
			lid = []
			for result in getId:
				lid.append(result['lid'])
			getId.close()
			lid = lid[0]
			addW = g.conn.execute('INSERT INTO Wine(grapetype,lid) VALUES (\'%s\',\'%s\')'%(grapetype,lid))
			addW.close()
			wineid = g.conn.execute('SELECT wid FROM Wine WHERE grapetype = \'%s\' AND lid = \'%s\''%(grapetype,lid))
			wid = []
			for result in wineid:
				wid.append(result['wid'])
			wineid.close()
			wid = wid[0]
		except:
			flash("Invalid Wine info")
			return redirect('/addWine')


		return redirect('/wineInfo/%s'%(wid))


	return render_template("addWine.html")

@app.route('/updateTag/<wid>', methods=['POST']) # FINISHED
def updateTag(wid):
	# check logged in and get uid
	if 'currUser' not in session:
		return redirect('/login')
	uid = session['currUser']

	old = []
	try:
		query = g.conn.execute('SELECT content FROM UserLikeTag WHERE uid = \'%s\' AND wid = \'%s\''%(uid,wid))
		for ele in query:
			old.append(ele['content'])
		query.close()
	except:
		pass

	new = request.form.getlist('tags')

	for item in new:
		if item not in old:
			# add like tag
			g.conn.execute('INSERT INTO UserLikeTag(content,uid,wid) VALUES (\'%s\',\'%s\',\'%s\')'% (item,uid,wid));

	for item in old:
		if item not in new:
			# unlike tag
			g.conn.execute('DELETE FROM UserLikeTag WHERE content = \'%s\' AND uid = \'%s\' AND wid = \'%s\''% (item,uid,wid));

	# return back to the original URL after finishing the action
	return redirect(request.referrer)

@app.route('/addTag/<wid>', methods=['POST']) # FINISHED
def addTag(wid):
	if 'currUser' not in session:
		return redirect('/login')
	uid = session['currUser']
	tag = request.form['new_tag']

	try:
		g.conn.execute('INSERT INTO UserLikeTag(content,uid,wid) VALUES (\'%s\',\'%s\',\'%s\')'% (tag,uid,wid));
	except:
		return redirect(request.referrer)
		flash('Tag already existed') 

	# return back to the original URL after finishing the action
	return redirect(request.referrer)

@app.route('/addWish/<wid>') # FINISHED
def addWish(wid):
	if 'currUser' not in session:
		return redirect('/login')

	uid = session['currUser']
	try:
		g.conn.execute('INSERT INTO UserWishWine(uid,wid) VALUES (\'%s\',\'%s\')'% (uid,wid));
	except:
		flash('Invalid') 

	return redirect(request.referrer)

@app.route('/addReview/<wid>', methods=['POST'])
def addReview(wid):
	if 'currUser' not in session:
		return redirect('/login')
	uid = session['currUser']
	title = request.form['Title']
	description = request.form['comment']
	point = int(request.form['Point'])

	try:
		g.conn.execute('INSERT INTO Review(uid,wid,title,description,point) VALUES (\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')'% (uid,wid,title,description,point));
	except:
		flash('Invalid') 

	return redirect(request.referrer)




