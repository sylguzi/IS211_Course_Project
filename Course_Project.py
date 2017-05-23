from flask import Flask, render_template
from flask import flash, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

DATABASE_PATH = 'database.sqlite'
TABLE = {
	'ACCOUNT': 'ACCOUNT',
	'POST': 'POST',
	'CATEGORY': 'CATEGORY'
}
conn = None

class User(object):
	def __init__(self, user):
		self.id, self.name, _ = user

class Post(object):
	def __init__(self, post):
		self.id, self.author_id, self.date, self.title, self.post, self.category_id, self.publish = post

class Category(object):
	def __init__(self, category):
		self.id, self.name = category

class DB_HELPER(object):
	"""Database helper"""
	def __init__(self, db):
		self.db = db
		self.__init_database()

	def __init_database(self):
		conn = sqlite3.connect(self.db)
		conn.execute('''create table if not exists ''' + TABLE['ACCOUNT'] + '''(
			ACCOUNT_ID	INTEGER PRIMARY KEY,
			NAME		TEXT NOT NULL,
			PASSWORD	TEXT NOT NULL)''')
		conn.execute('''create table if not exists ''' + TABLE['CATEGORY'] + '''(
			CATEGORY_ID	INTEGER PRIMARY KEY,
			NAME 		TEXT NOT NULL)''')
		conn.execute('''create table if not exists ''' + TABLE['POST'] + '''(
			ID 			INTEGER PRIMARY KEY,
			AUTHOR_ID	INTEGER NOT NULL,
			DATE 		DATE NOT NULL,
			TITLE		TEXT NOT NULL,
			POST		BLOB NOT NULL,
			CATEGORY_ID	INTEGER,
			PUBLISH		BOOLEAN,
			FOREIGN KEY (AUTHOR_ID) REFERENCES ''' + TABLE['ACCOUNT'] + '''(ACCOUNT_ID),
			FOREIGN KEY (CATEGORY_ID) REFERENCES ''' + TABLE['CATEGORY'] + '''(CATGEGORY_ID))''')
		conn.commit()
		conn.close()

	def select_user(self, name, password):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('SELECT * FROM ' + TABLE['ACCOUNT'] + ' where name = "' + name + '" and password = "' + password + '"')
		res = c.fetchone()
		conn.close()
		return User(res) if res is not None else None

	def check_if_row_exist(self, table, name):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('SELECT * FROM ' + table + ' where name = "' + name + '"')
		res = c.fetchone()
		conn.close()
		return res

	def insert_user(self, name, password):
		if self.check_if_row_exist(TABLE['ACCOUNT'], name) == None:
			conn = sqlite3.connect(self.db)
			conn.execute('INSERT INTO ' + TABLE['ACCOUNT'] + ' (name, password) VALUES ("' + name + '","' + password + '")')
			conn.commit()
			conn.close()
			return True
		else:
			return False

	def insert_category(self, name):
		if self.check_if_row_exist(TABLE['CATEGORY'], name) == None:
			conn = sqlite3.connect(self.db)
			conn.execute('INSERT INTO ' + TABLE['CATEGORY'] + ' (name) VALUES ("' + name + '")')
			conn.commit()
			conn.close()

	def select_post(self, id = None):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('SELECT * FROM ' + TABLE['POST'] + ' where ID = "' + str(id) + '"')
		res = c.fetchone()
		conn.close()
		return Post(res) if res is not None else None

	def delete_post(self, id):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('DELETE FROM ' + TABLE['POST'] + ' where ID = "' + str(id) + '"')
		conn.commit()
		conn.close()

	def insert_post(self, author_id, title, post, category_id = None):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('''
			INSERT INTO ''' + TABLE['POST'] + ''' (AUTHOR_ID, DATE, TITLE, POST, CATEGORY_ID, PUBLISH)
			VALUES (?,CURRENT_TIMESTAMP,?,?,?,1)''', (str(author_id), title, post, str(category_id) if category_id is not None else None))
		conn.commit()
		conn.close()

	def update_post(self, id, column, value):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('UPDATE ' + TABLE['POST'] + ' set ' + column + ' = "' + str(value) + '" where ID = "' + str(id) + '"')
		conn.commit()
		conn.close()

	def select_posts(self, author_id = None, publish = None):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		publish_filter = 'PUBLISH = ' + str(publish) if publish is not None else None
		author_filter = 'AUTHOR_ID = "' + author_id + '"' if author_id is not None else None

		where = ''
		if publish_filter is not None or author_filter is not None:
			if publish_filter is not None:
				if author_filter is not None:
					where = ' where ' + publish_filter + ' and ' + author_filter
				else:
					where = ' where ' + publish_filter
			else:
				where = ' where ' + author_filter

		c.execute('SELECT * FROM ' + TABLE['POST'] + where)
		res = c.fetchall()
		conn.close()
		return list(map(lambda x: Post(x), res))

def do_login(name, password):
	user = conn.select_user(name, password)
	if user is not None:
		session['logged_in'] = True
		session['user'] = {}
		session['user']['id'] = str(user.id)
		session['user']['name'] = user.name
		return redirect('/dashboard')
	else:
		flash('Something went wrong - user or password is incorrect!')
		return render_template('login.html')


@app.route('/login', methods=['POST'])
def submit_login():
	name = str(request.form['name'])
	password = str(request.form['password'])
	return do_login(name, password)

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/register')
def register():
	return render_template('register.html')

@app.route('/register', methods=['POST'])
def submit_register():
	name = str(request.form['name'])
	password = str(request.form['password'])
	res = conn.insert_user(name, password)
	if res:
		return do_login(name, password)
	else:
		flash('User already exists.')
		return render_template('register.html', form = request.form)

@app.route('/logout')
def logout():
	session['logged_in'] = False
	session['user'] = None
	return redirect('/')

@app.route('/post/<int:id>')
def show_post(id):
	id = str(id)
	if id is not None:
		post = conn.select_post(id)
		if post is not None:
			return render_template('post.html', post = post)
	flash('Invalid id: ' + id)
	return redirect('/')

@app.route('/post/create')
def post_create():
	if not session.get('logged_in', False):
		return redirect('/login')
	return render_template('edit_post.html')

def submit_post(id = None):
	if not session.get('logged_in', False):
		return redirect('/login')
	
	postTitle = request.form['title']
	postValue = request.form['post']
		
	if id is not None:
		post = conn.select_post(id)
		if str(post.author_id) != session['user']['id']:
			flash('This post doesn\'t belong to  you.')
			return redirect('/')
		if (postTitle != post.title):
			conn.update_post(id, 'TITLE', postTitle)
		if (postValue != post.post):
			conn.update_post(id, 'POST', postValue)
	else:
		conn.insert_post(session['user']['id'], postTitle, postValue)
	return redirect('/dashboard')

@app.route('/post/submit', methods=['POST'])
def submit_create_post():
	return submit_post()

@app.route('/post/submit/<int:id>', methods=['POST'])
def submit_update_post(id):
	return submit_post(id)

@app.route('/post/<int:id>/<string:action>')
def post_action(id, action):
	if not session.get('logged_in', False):
		return redirect('/')

	post = conn.select_post(id)
	if str(post.author_id) != session['user']['id']:
		flash('This post doesn\'t belong to  you.')
		return redirect('/')

	if action == 'edit':
		return render_template('edit_post.html', post = post)
	elif action == 'delete':
		conn.delete_post(id)
	elif action == 'publish':
		conn.update_post(id, 'PUBLISH', 1)
	elif action == 'unpublish':
		conn.update_post(id, 'PUBLISH', 0)

	return redirect('/dashboard')

@app.route('/dashboard')
# show user posts
def dashboard():
	if not session.get('logged_in', False):
		return redirect('/login')
	posts = conn.select_posts(session['user']['id'])
	return render_template('dashboard.html', posts = posts)

@app.route('/')
# show all posts [publish = True]
def index():
	posts = conn.select_posts(publish = 1)
	return render_template('index.html', session = session, posts = posts)

if __name__ == '__main__':
	conn = DB_HELPER(DATABASE_PATH)
	app.secret_key = os.urandom(12)
	app.run(debug = True, use_reloader=True)
