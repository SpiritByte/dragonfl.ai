#Import app from the init file, and other modules
from main import app, datab, login_user, url_for, redirect, render_template, flash
from main.form import Register, LoginForm
from main.model import User

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

print("started db script")

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://rythmhacks-4811d-default-rtdb.firebaseio.com/",
})

global ref 
ref = db.reference("Users")

@app.route("/")
def index():
  return render_template("index.html")

#Register route with post and get methods
@app.route("/register", methods = ["POST", "GET"])
def register_page():
    form = Register() #Create an instance of class
    if form.validate_on_submit(): #Once submitted, create a user with the data 
      user_to_create = User(username = form.username.data, email_address = form.email_address.data, 
                            password = form.password.data)
      #Add to database
      with app.app_context():
          datab.session.add(user_to_create)
          datab.session.commit()
          login_user(user_to_create)

      return redirect(url_for("dashboard_page"))
    
    if form.errors != {}:
      print(form.errors)
    return render_template("register.html", form = form)


@app.route("/login", methods = ["POST", "GET"])
def login_page():
  form = LoginForm()
  if form.validate_on_submit():
    attempted_user = User.query.filter_by(username = form.username.data).first()
    print(attempted_user)
    if attempted_user and attempted_user.check_password_correction(form.password.data):
        login_user(attempted_user)
        return redirect(url_for("dashboard_page"))
    
  return render_template('login.html', form = form)

@app.route("/dashboard")
def dashboard_page():
  global ref
  users = ref.get()
  return render_template("dashboard.html", users = users)