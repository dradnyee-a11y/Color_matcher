import os

import colorsys
import re
from flask import Flask, render_template, request, redirect, session
from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from functools import wraps
from PIL import Image, ImageColor

# Creat web application
app = Flask(__name__)
    
# Configure app to clear cookies after browser is closed
app.config["SESSION_PERMANENT"] = False
# Configure app to use filesystem 
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Configure the SQLite database
db = SQL("sqlite:///palettes.db")

# Secret key
app.secret_key = "cs50-secret-key"

# Helper functions
def get_dominant_color(image):
    # Open the image
    image = Image.open(image)
    # Reduce the image size for faster processing
    image = image.resize((150, 150))
    # Convert image to palette and get a single color
    result = image.convert("P", palette=Image.ADAPTIVE, colors=1)
    # Convert the color to RGB format
    dominant_color = tuple(result.getpalette()[:3])
    # Return the dominant color
    return dominant_color

def hex_simple(rgb):
    return '#%02x%02x%02x' % rgb

def rgb_to_hex(rgb):
    r, g, b = rgb
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    rgb = r, g, b
    return '#%02x%02x%02x' % tuple(rgb)

def complementary(hls):
    h, l, s = hls
    h = (h + 0.5) % 1.0
    h = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex(h)

def analogous(hls):
    h, l, s = hls
    h1 = (h + 1/12) % 1.0
    c1 = colorsys.hls_to_rgb(h1, l, s)
    c1 = rgb_to_hex(c1)
    h2 = (h - 1/12) % 1.0
    c2 = colorsys.hls_to_rgb(h2, l, s)
    c2 = rgb_to_hex(c2)
    return ([c1, c2])

def triadic(hls):
    h, l, s = hls
    h1 = (h + 1/3) % 1.0
    c1 = colorsys.hls_to_rgb(h1, l, s)
    c1 = rgb_to_hex(c1)
    h2 = (h + 2/3) % 1.0
    c2 = colorsys.hls_to_rgb(h2, l, s)
    c2 = rgb_to_hex(c2)
    return ([c1 , c2])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        else:
            return f(*args, **kwargs)
    return decorated_function

EXTENSIONS = {"png", "jpg", "jpeg"}
def file_validity(file):
    return "." in file and file.rsplit(".", 1)[1].lower() in EXTENSIONS

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
        confirm_password = request.form.get("confirm_password")
        
        # Ensure all the fields are filled
        if not username or not password or not confirm_password:
            return "Please fill out all fields", 400
        
        # Ensure the username is not too long
        if len(username) > 30:
            return "Username too long", 400
        
        # Ensure the password is not too short
        if len(password) < 6:
            return "Password too short", 400
        
        # Check if the paswswords match
        if password != confirm_password:
            return "Passwords do not match", 400
        
        # Hash password
        password = generate_password_hash(password)
        
        # Check for duplicate usernames
        try:
            # Insert the data into the database
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, password)
        except ValueError:
            return "Username already taken", 400
        return redirect("/login")
        

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    elif request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        
        # Ensure the user entered credentials 
        if not username or not password:
            return "Please enter your credentials", 400
        
        # Ensure the username is correct
        if len(user) != 1:
            return "Incorrect username", 400
        
        # Ensure the password is correct
        elif not check_password_hash(user[0]["hash"], password):
            return "Incorrect password", 400
        
        # Log the user in by starting a session
        session["user_id"] = user[0]["id"]
        session["username"] = user[0]["username"]
    return redirect("/")

@app.route("/logout")
@login_required
def logout():
    # Log the user out by clearing the session
    session.clear()
    return redirect("/")

@app.route("/wheel")
def wheel():
    return render_template("wheel.html")

@app.route("/my_palettes", methods=["GET", "POST"])
@login_required
def my_palettes():
    user_id = session["user_id"]
    if request.method == "GET":
        palettes = db.execute("SELECT * FROM combos WHERE user_id = ?", user_id)
        return render_template("saved.html", palettes=palettes)
    
    elif request.method == "POST":
        action = request.form.get("action")
        name = request.form.get("palette_name")
        if not name:
            name = "Untitled Palette"
        
        # Proceed if the action has value save_palette
        if action == "save_palette":   
            base_color = request.form.get("base_color")
            complementary = request.form.get("complementary")
            analogous = request.form.get("analogous")  
            triadic = request.form.get("triadic")
            
            # Ensure the colors exist
            if not base_color or not complementary or not analogous or not triadic:
                return "Invalid Palette", 400
            
            # Save the palette in the database
            db.execute("INSERT INTO combos (user_id, base_color, complementary, analogous, triadic, name) VALUES (?, ?, ?, ?, ?, ?)", 
                       user_id, base_color, complementary, analogous, triadic, name)

            return redirect("/my_palettes")

@app.route("/color_matcher", methods=["GET", "POST"])
def color_matcher():
    # set tab to pick by default 
    tab = "pick"
    hex_color = None
    image_uploaded = False
    color = None
    palettes = {}

    if request.method == "POST":
        # If the user uploaded an image, set tab to upload
        if "image" in request.files and request.files.get("image"):
             
             image = request.files.get("image")

             # Ensure the user uploaded an image
             if not image or image.filename == "":
                return "No image uploaded", 400
             
             # Ensure the file type is supported
             if not file_validity(image.filename):
                return "Invalid file type", 400
             
             # Get the dominant color from the image
             dominant_color = get_dominant_color(image)
             hex_color = hex_simple(dominant_color)

            # Ensure a color was extracted
             if hex_color is None:
                return "Could not extract color from image", 400
            
            # Decide which tab to show
             tab = "upload"
             image_uploaded = True

        # If the user picked a color, set tab to pick
        elif "color" in request.form:
            color = request.form.get("color")
            hex_color = color

            # Ensure hex_color is a hex value
            if not re.match(r"^#[0-9A-Fa-f]{6}$", hex_color):
                return "Invalid Color", 400
            
            # Ensure the user picked a color
            if hex_color is None:
                return "No color selected", 400
            
            # Decide which tab to show
            tab = "pick"
        
        # Convert hex to RGB to convert it to HSL
        rgb = ImageColor.getrgb(hex_color)
        hls = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        # Generate color palettes
        palettes["Complementary"] = [complementary(hls)]
        palettes["Analogous"] = analogous(hls)
        palettes["Triadic"] = triadic(hls)

    return render_template("color_matcher.html", extracted_color=hex_color, tab=tab, palettes=palettes, color=color, image_uploaded=image_uploaded)
