#Import necessary modules
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm

#Initialize flask app, with database and security key
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///test.db' #Configure a DB using SQLite
app.config['SECRET_KEY'] = 'e5c905100a086b1d7cb9a75f' #Configure a security key to ensure a secure connection

#Create database
datab = SQLAlchemy()
datab.init_app(app)

#Bcrypt class to store hashed passwords
bcrypt = Bcrypt(app)

#Use flask_login built in login class for users
loginmanager = LoginManager(app)

#Import the app's routes
from main import routes
