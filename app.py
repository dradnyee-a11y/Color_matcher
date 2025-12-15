import os
import colorsys
from flask import Flask, render_template, request, redirect, session, flash
from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from functools import wraps
from PIL import Image, ImageColor

# Creat web application
app = Flask(__name__)

# Ensure the app runs on main
if __name__ == "__main__":
    app.run()
    
# Configure app to clear cookies after browser is closed
app.config["SESSION_PERMANENT"] = False
# Configure app to use filesystem 
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Configure the SQLite database
db = SQL("sqlite:///outfits.db")

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

def hex(rgb):
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
    # Get data from the function passed in
    @wraps(f)

    def decorated_function(*args, **kwargs):
        # If the user is not logged in, redirect to login page
        if session.get("user_id") is None:
            return redirect("/login")
        
        # Otherwise, proceed with the original function
        else:
            return f(*args, **kwargs)
    
    # return the decorated function
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # If reached via GET, show the form
    if request.method == "GET":
        return render_template("register.html")
    
    # If reached via POST
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        # Check if the paswswords match
        if password != confirm_password:
            return "Passwords do not match", 400
        
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
    # If reached via GET, show the form
    if request.method == "GET":
        return render_template("login.html")
    
    # If reached via POST
    elif request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        print(user)
        if user is None:
            return "list empty", 400
        
        # Ensure the user entered credentials 
        if not username or not password:
            return "Please enter your credentials", 400
        
        # Ensure the password is correct
        if len(user) != 1:
            return "Incorrect username", 400
        
        elif not check_password_hash(user[0]["hash"], password):
            return "Incorrect password", 400
        
        # Log the user in by starting a session
        session["user_id"] = user[0]["id"]
        session["username"] = user[0]["username"]
    return redirect("/")

@app.route("/logout")
def logout():
    # Log the user out by clearing the session
    session.clear()
    return redirect("/login")

@app.route("/wheel")
def wheel():
    return render_template("wheel.html")

@app.route("/debug", methods=["POST"])
def debug():
    if request.method == "POST":
        print("FORM DATA:", request.form)
        return "Received"
    return render_template("saved.html")

@app.route("/combos", methods=["GET", "POST"])
@login_required
def combos():
    user_id = session["user_id"]
    if request.method == "GET":
        palettes = db.execute("SELECT * FROM combos WHERE user_id = ?", user_id)
        print("palettes:", palettes)
        return render_template("saved.html", palettes=palettes)
    
    elif request.method == "POST":
        action = request.form.get("action")
        name = request.form.get("palette_name")
        if not name:
            name = "Untitled Palette"
        
        if action == "save_palette":
            base_color = request.form.get("base_color")
            print("base color:", base_color)
            complementary = request.form.get("complementary")
            print("complementary:", complementary)
            analogous = request.form.get("analogous")  
            print("analogous:", analogous) 
            triadic = request.form.get("triadic")
            print("triadic:", triadic)

            if complementary == '':
                return "no hex", 500
            
            # Save the palette to the database
            db.execute("INSERT INTO combos (user_id, base_color, complementary, analogous, triadic, name) VALUES (?, ?, ?, ?, ?, ?)", 
                       user_id, base_color, complementary, analogous, triadic, name)

            flash ("Palette saved!", "success")
            return redirect("/combos")

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
             print("form:", request.form)

             # Ensure the user uploaded an image
             if not image:
                return "No image uploaded", 400
             
             # Get the dominant color from the image
             dominant_color = get_dominant_color(image)
             hex_color = hex(dominant_color)

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

            # Ensure the user picked a color
            if hex_color is None:
                return "No color selected", 400
            
            # Decide which tab to show
            tab = "pick"
        
        # Convert hex to RGB to convert it to HSL
        rgb = ImageColor.getrgb(hex_color)
        print("Hex:", hex_color)
        print ("RGB:", rgb)
        hls = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        print ("HLS:", hls)

        # Generate color palettes
        palettes["Complementary"] = [complementary(hls)]
        print ("Complementary:",palettes["Complementary"])
        palettes["Analogous"] = analogous(hls)
        print ("Analogous:",palettes["Analogous"])
        palettes["Triadic"] = triadic(hls)
        print ("Triadic:",palettes["Triadic"])

        if palettes is None:
            return "Could not generate color palettes", 400

    return render_template("color_matcher.html", extracted_color=hex_color, tab=tab, palettes=palettes, color=color, image_uploaded=image_uploaded)
