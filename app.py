######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string' 

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Invalid password or email try again</a>\
		</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		gender=request.form.get('gender')
		dob=request.form.get('dob')
		hometown=request.form.get('hometown')
		fname=request.form.get('fname')
		lname=request.form.get('lname')

	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES ('{0}', \
		       '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, gender, dob, hometown, fname, lname)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return "<a href='/login'>Try again</a> </br><a href='/register'>or make an account</a>"

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getAlbumIdFromUsers(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

#get tag_id from Tag name
def getTagIdFromTagName(tag_name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(tag_name))
	return cursor.fetchone()[0]


#get photo_ids corresponding to one tag
def getPhotosFromTagId(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT Photos.imgdata, Photos.photo_id, Photos.caption FROM Photos, Tagged WHERE \
		Photos.photo_id = Tagged.photo_id AND Tagged.tag_id = '{0}'".format(tag_id))
	return cursor.fetchone()[0] #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (user_id, caption, imgdata) VALUES (%s, %s, %s)''', (uid, caption, photo_data))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

#upload photo to an album
@app.route('/uploadtoalbum/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_to_album(album_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (user_id, caption, imgdata, album_id) VALUES (%s, %s, %s, %s)''',\
		  (uid, caption, photo_data, album_id))
		conn.commit()
		#take it to upload photos wiht specific album id
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', album_id=album_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('uploadtoalbum.html', album_id=album_id)

#begin friend adding code
@app.route('/addfriend', methods=['GET', 'POST'])
@flask_login.login_required
def add_friend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fid = getUserIdFromEmail(request.form.get('email'))
		cursor = conn.cursor()
		#insert friend into friendship table
		cursor.execute('''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid, fid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Friend added!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('addfriend.html')
#end friend adding code

#begin create album code
@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		Name = request.form.get('Name')
		date_of_creation = request.form.get('date_of_creation')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (Name, date_of_creation, user_id) VALUES (%s, %s, %s)''', (Name, date_of_creation, user_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!', photos=getUsersPhotos(user_id), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('create_album.html')
#end create album code

#begin delete album code
@app.route('/deletealbum/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album(album_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		#delete the album with specified name and user_id
		cursor.execute("DELETE FROM Albums WHERE user_id, album_id = '{0}'".format(uid, album_id))
		conn.commit()
		#delete the photos inside the album
		cursor.execute("DELETE FROM Photos WHERE album_id = '{0}'".format(album_id))
		return render_template('hello.html', name=flask_login.current_user.id, message='Album deleted!', album_id = album_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('deletealbum.html', album_id = album_id)
#end delete album code

#begin delete photo code
@app.route('/deletephoto/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo(photo_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(photo_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo deleted :(', photo_id=photo_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('deletephoto.html', photo_id=photo_id)
#end delete photo code

#begin add tag code
@app.route('/addtag/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def addtag(photo_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		tag_name = request.form.get('tag_name')
		tag_id = getTagIdFromTagName(tag_name)
		cursor.execute('''INSERT INTO Tagged(photo_id, tag_id) VALUES (%s, %s)''', (photo_id, tag_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Tag added!', photo_id=photo_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('addtag.html', photo_id=photo_id)
#end add tag code

#begin view all photos by tag
@app.route('/viewphotosbytag', methods=['GET', 'POST'])
@flask_login.login_required
def view_photos_by_tag():
	#display photos under this tag
	if request.method == 'GET':
		tag_name = request.form.get('tag_name')
		tag_id = getTagIdFromTagName(tag_name)
		return render_template('viewphotosbytag.html', photos=getPhotosFromTagId(tag_id), base64=base64)
	else:
		return render_template('viewphotosbytag.html')
	
#begin view all photos by tag
@app.route('/viewuserphotosbytag', methods=['GET', 'POST'])
@flask_login.login_required
def view_user_photos_by_tag():
	#display photos under this tag
	if request.method == 'GET':
		tag_name = request.form.get('tag_name')
		tag_id = getTagIdFromTagName(tag_name)
		uid = getUserIdFromEmail(flask_login.current_user.id)

		return render_template('viewphotosbytag.html', photos=getPhotosFromTagId(tag_id), base64=base64)
	else:
		return render_template('viewphotosbytag.html', photos=getPhotosFromTagId(tag_id), base64=base64)

#begin view friends
@app.route('/mostpopulartags', methods=['GET', 'POST'])
@flask_login.login_required
def most_popular_tags():
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT name, COUNT(name) FROM Tags NATURAL JOIN Tagged GROUP BY tag_id ORDER BY COUNT(tag_id) DESC LIMIT 3")
		return render_template('mostpopulartags.html', tags=cursor.fetchall())
	else:
		return render_template('mostpopullartags.html', tags=cursor.fetchall())

#begin add comment code
@app.route('/addcomment/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def addcomment(photo_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		comment = request.form.get('comment')
		date = request.form.get('date')
		cursor.execute('''INSERT INTO Comments(text, date, user_id, photo_id) VALUES (%s, %s, %s, %s)''', (comment, date, uid, photo_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Comment added!', photo_id=photo_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('addcomment.html', photo_id=photo_id)
#end add comment code

#begin like code
@app.route('/like/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def like(photo_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Likes(user_id, photo_id) VALUES (%s, %s)''', (uid, photo_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo liked!', photo_id=photo_id, photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('like.html', photo_id=photo_id)
#end like code

#begin number of likes code
@app.route('/numberoflikes/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def number_of_likes(photo_id):
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) AS ccount FROM Likes WHERE photo_id = '{0}'".format(photo_id))
		return render_template('numberoflikes.html', likes=cursor.fetchone()[0])
	else:
		return render_template('numberoflikes.html')
#end number of likes code

#begin view album code
@app.route('/viewalbum', methods=['GET', 'POST'])
@flask_login.login_required
def view_album():
	#display users albums
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT Name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
		return render_template('viewalbum.html', albums=cursor.fetchall())
	else:
		return render_template('viewalbum.html')
#end view album code

#begin view friends
@app.route('/viewfriends', methods=['GET', 'POST'])
@flask_login.login_required
def view_friends():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT Users.email FROM Users, Friendship WHERE Friendship.UID2 = Users.user_id AND \
		  Friendship.UID1 = '{0}'".format(uid))
		return render_template('viewfriends.html', friends=cursor.fetchall())
	else:
		return render_template('viewfriends.html')

#begin view friend's album code
@app.route('/viewfriendsalbums', methods=['GET', 'POST'])
@flask_login.login_required
def view_friend_album():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT Albums.Name, Albums.album_id, Users.fname FROM Albums, Friendship, Users WHERE \
		 Users.user_id = Friendship.UID2 AND Friendship.UID2 = Albums.user_id \
		 AND Friendship.UID1 = '{0}'".format(uid))
		return render_template('viewfriendsalbums.html', albums=cursor.fetchall())
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('viewfriendsalbums.html')
#end view friend's album code

#show photos in album
@app.route('/viewalbumphotos/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def view_album_photos(album_id):
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, caption, photo_id FROM Photos WHERE album_id = '{0}'".format(album_id))
		return render_template('viewalbumphotos.html', album_id = album_id, photos=cursor.fetchall(), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('viewalbumphotos.html')

#show photos in friends album
@app.route('/viewfriendsalbumsphotos/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def view_friends_album_photos(album_id):
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, caption FROM Photos WHERE album_id = '{0}'".format(album_id))
		return render_template('viewfriendsalbumsphotos.html', album_id=album_id, photos=cursor.fetchall(), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('viewfriendsalbumsphotos.html')

#begin view friend's photos code
@app.route('/viewfriendphotos', methods=['GET', 'POST'])
@flask_login.login_required
def view_friend_photos():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fid = getUserIdFromEmail(request.form.get('email'))
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(fid))
		return cursor.fetchall()
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('viewfriendphotos.html')
#end view friend's photos code

#browse all photos
@app.route('/browsephotos', methods=['GET', 'POST'])
def browse_photos():
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT Photos.imgdata, Photos.photo_id, Photos.caption FROM Photos")
		photos=cursor.fetchall()
		return render_template('browsephotos.html', photos=photos, base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('browsephotos.html')
	
#browse all photos
@app.route('/browsealbums', methods=['GET', 'POST'])
def browse_albums():
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT Albums.Name, Users.fname, Albums.album_id FROM Albums, Users")
		return render_template('browsealbums.html', albums=cursor.fetchall())
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('browsealbums.html')

#search users
@app.route('/searchusers', methods=['GET', 'POST'])
def search_users():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT Users.email FROM Users WHERE Users.email = '{0}'".format(request.form.get('email')))
		return render_template('searchusers.html', users=cursor.fetchall())
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('searchusers.html')

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
