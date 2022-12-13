import flask
from flask import Flask,request, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from bcrypt import gensalt, hashpw, checkpw

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:XjGEYiGZFj3ofqlD@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'Drmhze6EPcv0fN_81Bj-nT'
db = SQLAlchemy(app)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title:str, body:str, owner_id:int):
        self.title = title
        self.body = body
        self.owner = owner_id

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', back_populates='owner')

    def __init__(self, username:str, password:str):
        self.username = username
        self.password = password

def feedback(new_feedback_message):
    global feedback_message
    feedback_message = ""
    if feedback_message != "" or feedback_message == None:
        feedback_message += "<br>" + new_feedback_message
    else:
        feedback_message = new_feedback_message
    return feedback_message

#Get the total count of ids in the database blog table.
def get_post_total():
    blog_ids = []
    with app.app_context():
        blogs = (db.session.query(Blog.id).all())
        for row in blogs:
            blog_id = str(row["id"])
            blog_ids.append(blog_id)
        post_total = len(blog_ids)
        return post_total

#Take input, create object, and add it to the database.
def create_blog(title:str, body:str, owner_id:int):
    newblog = Blog(title, body, owner_id)
    alter_database(newblog)

#Take input object and add it to the database.
def alter_database(object):
    with app.app_context():
        try:
            db.session.add(object)
        except:
            db.session.rollback()
            raise
        else:
            db.session.commit()

#Get all the post titles and bodies in the table.
def get_posts():
    blog_output = []
    with app.app_context():
        #Query the database for all the titles and bodies in the table.
        blogs = (db.session.query(Blog.title,Blog.body).all())
        for row in blogs:
            blog_title = str(row["title"])
            blog_output.append(blog_title)
            blog_body = str(row["body"])
            blog_output.append(blog_body)
        return blog_output

@app.before_request
def require_login():
    #List routes user can access.
    allowed_routes = ['login', 'signup', 'index', 'blog']
    #Block user from routes not listed and allow the user to access the site css file while not being logged in.
    if request.endpoint not in allowed_routes and 'username' not in session and not (request.path in ['/static/site.css']):
        print("Not logged in. Rerouting")
        return flask.redirect(url_for("login"))

#Reroute all of requests to to /blog.
@app.route("/")
def index():
    return flask.render_template("index.html")

#User signup page
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == 'GET':
        return flask.render_template("signup.html")
    
    if request.method == 'POST':
        if 'username_feedback' in locals():
            del username_feedback
        if 'password_feedback' in locals():
            del username_feedback
        if 'verify_feedback' in locals():
            del username_feedback
        if 'username' in locals():
            del username
        if 'password' in locals():
            del password
        if "verify" in locals():
            del verify

        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        #Validate user's data
        if username == "":
            username_empty = "Please enter a username."
            feedback(username_empty)
            username_feedback = username_empty
        if username != "":
            if len(username) <= 2:
                short_username = "The username entered is too short. It must be at least 3 characters long."
                feedback_message(short_username)
                username_feedback = short_username

        #Username looks good check the password.
        if password == "":
            password_empty = "Please enter a password."
            password_feedback = password_empty
            feedback(password_empty)
        if verify == "":
            verify_empty = "Please enter your password above to verify it was typed correctly."
            feedback(verify_empty)
            verify_feedback = verify_empty
        if len(password) <= 3:
            short_password = "The password entered is too short. Passwords must be 3 characters or more."
            feedback(short_password)
            password_feedback = short_password

        #Check that the password was typed correctly twice.
        if password != verify:
            passwords_not_equal = "The two passwords entered do not match. Re-enter and try again."
            feedback(passwords_not_equal)
            verify_feedback = passwords_not_equal
        
        #If feedback for the user input exists display it to the user
        if 'feedback_message' not in locals() or feedback_message != "":
            if 'username_feedback' in locals() and 'password_feedback' in locals() and 'verify_feedback' in locals():
                return flask.render_template('signup.html',
                    usernameFeedback = username_feedback,
                    passwordFeedback = password_feedback,
                    verifyFeedback = verify_feedback,
                    feedback = feedback_message,
                    username = username)
            elif 'password_feedback' in locals() and 'verify_feedback' in locals():
                return flask.render_template('signup.html',
                    passwordFeedback = password_feedback,
                    verifyFeedback = verify_feedback,
                    feedback = feedback_message,
                    username = username,
                    password = password)
            
            elif 'username_feedback' in locals() and 'verify_feedback' in locals():
                return flask.render_template('signup.html',
                    usernameFeedback = username_feedback,
                    verifyFeedback = verify_feedback,
                    feedback = feedback_message,
                    password = password)

            elif 'username_feedback' in locals():
                return flask.render_template('signup.html',
                    usernameFeedback = username_feedback,
                    feedback = feedback_message,
                    password = password,
                    verify=verify)

            elif 'verify_feedback' in locals():
                return flask.render_template('signup.html',
                    verifyFeedback = verify_feedback,
                    feedback = feedback_message,
                    username = username,
                    password = password)

        #If there is no feedback then see if the username exists already.
        check_exist = username
        existing_user = User.query.filter_by(username=check_exist).first()
        if not existing_user:
            salt = gensalt()
            hash = hashpw(password.encode('utf-8'), salt)
            new_user = User(username, hash)
            alter_database(new_user)
            session['username'] = username
            return flask.redirect(url_for("blog"))
        else:
            #If th eusername does exist let the user know.
            username_feedback = "User already exists."
            feedback(username_feedback)
            return flask.render_template('signup.html',
            usernameFeedback = username_feedback,
            username=username,
            password=password,
            verify=verify,
            feedback = feedback_message)

#User login page
@app.route("/login", methods=["GET","POST"])
def login():
    if session.get('username')==True:
        return flask.redirect("/blog")

    if request.method == 'GET':
        return flask.render_template("login.html")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        #Check does the username exist in the database.
        check_exist = username
        existing_user = User.query.filter_by(username=check_exist).first()
        if not existing_user:
            username_feedback = """That username doesn't exist. Maybe you need to create an account. <a href='/signup' id='feedbackLink'>Create an account here.</a>"""
            feedback(username_feedback)
            feedback_message = username_feedback
            return flask.render_template('login.html',
            usernameFeedback = username_feedback,
            feedback = feedback_message)
        #Check that the credentials are valid.
        user = User.query.filter_by(username=username).first()
        try:
            if checkpw(password.encode("utf-8"),user.password.encode("utf-8")):
                #Log user in by adding session variable.
                session['username'] = username
                return flask.redirect(url_for("newpost"))
            else:
                wrong_password = "The password entered is incorrect."
                feedback(wrong_password)
                password_feedback = wrong_password
                return flask.render_template('login.html',
                username = username,
                passwordFeedback = password_feedback,
                feedback = feedback_message)
        except ValueError:
            no_hashed_password_feedback = "Uh oh! Your user doesn't have a hashed password it seems. Try creating a new account. Sorry for the inconvenience."
            feedback_message = no_hashed_password_feedback
            return flask.render_template('login.html',
                username = username,
                usernameFeedback = feedback_message,
                password = password,
                passwordFeedback = feedback_message,
                feedback = feedback_message)
        

#Display all posts or single post
@app.route("/blog",methods=["GET"])
def blog():
    if request.args.get('id'):
        id = int(request.args.get('id'))
        #If the id provided is more than the ids in the database or equal to 0 reroute it to /blog.
        if id > get_post_total() or id == 0:
            return flask.redirect(url_for("blog"))
        #If the id provided is good look up the post
        else:
            with app.app_context():
                print("Query for the singel post.")
                #Query the database for the post's title and body based on the id in the URL.
                blogs = (db.session.query(Blog.title,Blog.body).filter(Blog.id == id))
                for row in blogs:
                    blog_title = str(row["title"])
                    blog_body = str(row["body"])
                    print(blog_title)
            #Return the single post to user
            return render_template("post.html",
            title = blog_title,
            body = blog_body)
    #Display all the posts
    else:
        blogs = get_posts()
        titles = []
        bodies = []
        i = 0
        for blog in blogs:
            mod = i % 2
            #Get every even item in the list and add it to the list of blog bodies.
            if mod > 0:
                bodies.append(blog)
                i += 1
            #Get every odd item in the list and add it to the list of blog titles.
            else:
                titles.append(blog)
                i += 1
        #Return all of the posts to user
        return render_template("blog.html",
        titlesLen = len(titles),
        titles = titles,
        bodies = bodies)

#Render a form to create a new post.
@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if request.method == 'GET':
        return render_template("blogform.html")
    else:
        #Take the form input check it, provide feedback if needed about form input, and submit the input to database.
        need_title = "Please enter a title for your blog."
        need_body = "Please enter a body."
        blog_title = request.form['title']
        blog_body = request.form['body']
        #If title input is empty provide feedback.
        if blog_title == "" or blog_title == " ":
            feedback_message = need_title
            #If title and body input is empty provide feedback.
            if blog_body == "" or blog_body == " ":
                feedback_message = "Please enter a title for you blog and enter a body."
                return render_template("blogform.html",
            title = blog_title,
            needTitle = need_title,
            body = blog_body,
            needBody = need_body,
            feedback = feedback_message)
            else:
                return render_template("blogform.html",
            title = blog_title,
            needTitle = need_title,
            body = blog_body,
            feedback = feedback_message)

        #If body input is empty provide feedback.
        if blog_body == "" or blog_body == " ":
            feedback_message = need_body
            return render_template("blogform.html",
            title = blog_title,
            body = blog_body,
            needBody = need_body,
            feedback = feedback_message)
        
        #If the input looks good commit create the database entry and reroute to page showing the new post.
        else:
            user = User.query.filter_by(username=session['username']).first()
            create_blog(blog_title, blog_body, user.id)
            new_post = "blog" + str(get_post_total())
            return flask.redirect((new_post))

@app.route('/logout')
def logout():

    if session.get('username')==True:
        return flask.redirect("/")
    else:
        session.pop('username', None)
        return flask.redirect("/")

if __name__ == "__main__":
    app.run()
