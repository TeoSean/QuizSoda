from flask import Flask, render_template, request, redirect, url_for, make_response
from hashlib import sha256
import sqlite3
from auth import SessionManager, AccountManager

app = Flask(__name__)

def checkLoggedIn(request):
    session = SessionManager('database.db')
    check = session.get_session(request.cookies)
    if check == None: #if not logged in or if sessionID is wrong
        return False
    else:
        return check

@app.route('/')
def index():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return render_template('index.html', navBarPage="home", authenticated=False)
    else: # if logged in
        return render_template('index.html', navBarPage="home", authenticated=True)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        loggedIn = checkLoggedIn(request)
        if loggedIn == False: #if not logged in or if sessionID is wrong
            resp = make_response(render_template('login.html', navBarPage="login", authenticated=False))
            resp = SessionManager('database.db').remove_session(request.cookies, resp) 
            # clear out the session id cookie for clean login (this func also removes the token from the db but since token does not exist nothing happens)
            return resp
        else: # if logged in
            return redirect(url_for('index'))

    if request.method == "POST":
        account = AccountManager('database.db')
        resp = account.login(request)
        return resp

    
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "GET":
        session = SessionManager('database.db')
        check = session.get_session(request.cookies)
        if check == None: #if not logged in or if sessionID is wrong
            resp = make_response(render_template('register.html', navBarPage="register", authenticated=False))
            resp = session.remove_session(request.cookies, resp) 
            # clear out the session id cookie for clean register (this func also removes the token from the db but since token does not exist nothing happens)
            return resp
        else: # if logged in
            return redirect(url_for('index'))

    elif request.method == "POST":
        # since this application is meant to be small I really don't mind slapping all the validation here
        username, password, passwordConfirm = request.form['username'], request.form['password'], request.form['passwordConfirm']
        if password != passwordConfirm:
            return render_template('register.html', navBarPage='register', message='Your passwords do not match. Please try again.', authenticated=False)
        
        # check for username already exists
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("SELECT username FROM users WHERE username=?", (username, ))
            if len(cur.fetchall()) != 0:
                return render_template('register.html', navBarPage='register', message='Invalid username.', authenticated=False)

        except Exception as e:
            print(e)
            return render_template('register.html', navBarPage='register', message='There was an unexpected error. Please contact an admin.', authenticated=False)
        
        try:
            passwordHash = sha256(password.encode('utf-8')).hexdigest()
        except Exception as e:
            print(e)
            return render_template('register.html', navBarPage='register', message='There was an unexpected error. Please contact an admin.', authenticated=False)
        
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("INSERT INTO users VALUES(?, ?)", (username, passwordHash))
            con.commit()

        except Exception as e:
            print(e)
            return render_template('register.html', navBarPage='register', message='There was an unexpected error. Please contact an admin.', authenticated=False)
        
        # successfully registered! (set as authenticated and redirect to home)
        session = SessionManager('database.db')
        resp = make_response(redirect(url_for('index')))
        resp = session.create_session(username, resp)
        return resp

@app.route('/challenges')
def challenge():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else: # if logged in
        return render_template('generatedTemplate.html', navBarPage="challenges", authenticated=True)

@app.route('/account')
def account():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else:
        username = loggedIn
        
    return render_template('account.html', navBarPage="account", authenticated=True, username=username) # TEST VALUES MISSING: placing, points

app.run(port=5000, host='0.0.0.0', debug=True)