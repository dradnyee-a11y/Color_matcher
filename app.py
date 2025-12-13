import os
import io
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from functools import wraps
from PIL import Image



app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "outfits.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

def get_dominant_color(image):
            image = Image.open(image)
            image = image.resize((150, 150))
            result = image.convert("P", palette=Image.ADAPTIVE, colors=1)
            dominant_color = tuple(result.getpalette()[:3])
            return dominant_color

def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % tuple(rgb)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password = generate_password_hash(password)
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            return "Passwords do not match", 400
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
        except ValueError:
            return "Username already taken", 400
        

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT password FROM users WHERE username = ?", (username))
        if not username or not password:
            return "Invalid credentials", 400
        if user["password"] != password:
            return "Incorrect password", 400
    session["user_id"] = user["id"]
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/saved")
@login_required
def saved():
    return render_template("saved.html")

@app.route("/color_matcher", methods=["GET", "POST"])
def color_matcher():
    tab = "pick"
    hex_color = None
    if request.method == "POST":
        image = request.files.get("image")
        if not image:
            return "No image uploaded", 400
        elif image:
            dominant_color = get_dominant_color(image)
            hex_color = rgb_to_hex(dominant_color)
        if "image" in request.files:
             tab = "upload"
        elif "color" in request.form:
             tab = "pick"
    return render_template("color_matcher.html", extracted_color=hex_color, tab=tab)
