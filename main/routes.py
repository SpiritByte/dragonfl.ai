#Import app from the init file
from main import app

@app.route("/")
def home_page():
  return "Hello World"

