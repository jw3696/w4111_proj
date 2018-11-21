'''
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1>Hello World!</h1>"
'''

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, abort,flash
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
#login_manager = LoginManager()
#login_manager.init_app(app)

DB_USER = "hz2562"
DB_PASSWORD = "dp99rrq9"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

#engine.execute("""DROP TABLE IF EXISTS test;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS test ( id serial, name text UNIQUE );""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

engine.execute("""DROP TABLE IF EXISTS testUser;""")
engine.execute("""CREATE TABLE IF NOT EXISTS testUser ( id serial, name text UNIQUE, password text );""")

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
	SELECT winery, grapeType \
	FROM (PopWine P JOIN Wine W ON P.wid = W.wid) AS PW JOIN Location L \
	ON PW.lid = L.lid;")
	names = []
	for result in cursor:
		names.append('Winery: %s , Grape: %s'%(result['winery'],result['grapetype']))  # can also be accessed using result[0]
	cursor.close()

	context = dict(data = names)
	return render_template("index.html", **context)

@app.route('/addUser', methods=['POST'])
def addUser():
	name = request.form['name']
	psw = request.form['psw']
	print(name)
	print(psw)
	#cmd = 'INSERT INTO testUser VALUES (:name)';
	try:
		g.conn.execute('INSERT INTO testUser(name,password) VALUES (\'%s\',\'%s\')'% (name,psw));
	except:
		flash("User name already exist")
		return redirect('/signup')

	return redirect('/')

@app.route('/signup')

def signup():
	return render_template("signup.html")

username = None
login = False

@app.route('/login')
def login():
	name = request.form['name']
	psw = request.form['psw']
	try:
		g.conn.execute('SELECT * FROM testUser WHERE name=\'%s\', password = \'%s\''%(name, psw))
		username = name
		login = True
	except:
		flash('invalid username or password')


@app.route('/user/<id>')
def user(id):
	if login == False:
		redirect('/login')

def another():
 	return render_template("signup.html")

@app.route('/wineInfo')
def wineInfo():
	return render_template("wineInfo.html")

@app.route('/search')
def search():
	return render_template("search.html")

@app.route('/noWine')
def noWine():
	return render_template("noWine.html")

@app.route('/addWine')
def addWine():
	return render_template("addWine.html")



