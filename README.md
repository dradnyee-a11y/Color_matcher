# Color Combination Finder
### Video Demo:  <URL HERE>
### Description:
#### Overview of project
Color combination Finder is a web application that generates complementary, analogous and triadic palettes for a chosen color. The user can either select a color (or enter RGB values) or upload an image from which the app extracts the dominant color, generates and displays palettes. The app reduces struggle of manually finding color palettes, making it easy to find colors that go well.\
The app offers the following features: users can login, register, save and view palettes (only if logged in) and use the navbar to easily navigate across the website.


#### User Interface 
The user reaches the home page by the default route after opening the app. At the top is a navbar that contains the links to homepage, generating palette, saved palettes(My palettes) and color wheel which provides minimal information about the use of palettes; as well as login, register and if already logged in, logout.

The homepage displays the title and brief introduction. The user can click the get started button which redirects to generate palettes page

The generate Palettes page has two tabs: Pick A Color and Upload An Image. The Pick a color tab displays a color picker by which the user can choose a color and after they click find combinations button, selected color and color combinations are displayed. The user can optionally save the palette which requires login, by submitting a form. Similarly, the Upload an Image tab lets the user upload the image; then after clicking extract color and find combinations extracts the dominant color and displays combinations.

The color wheel page features a picture of a color wheel and basic information about the use of the palettes. It can be accessed by clicking the link on the navbar as well as by clicking the link on generate palettes page. 

If the user chooses to save the palette, they are redirected to My palettes after logging in if not done before. Otherwise, the user can anytime visit the page by clicking on My palettes link on the navbar. All of the user's saved palettes are displayed here along with hex color codes and the submitted title (if any) by the user. 

#### app.py (Controller)
This is the main flask application which controls routes, user authentication, processing user input, sessions and data from the database. As the backend of the application, it checks for errors against malicious input and validates user input. The logic for extracting dominant color from images, calculating hex values for color palettes and saving palettes is in this file. It is  the medium through which data is retrieved from and entered into the database, connecting the database and templates.

#### /templates (View)
Templates directory contains the HTML used for the application. layout.html contains the content for common features like navbar and footer and uses the body from templates. index.html displays the homepage.color_matcher.html displays the Generate palettes page. It displays the two tabs and when submitted via POST, it renders palettes using the data passed by app.py. saved.html displays saved palettes, displaying the saved palettes using the data from backend. wheel.html displays the color wheel page and login.html and register.html display login and register pages respectively. As the templates use jinja, the data is dynamically displayed. 

#### /static
To enhance the appearance of the html of this application, in static directory is the file style.css which contains some CSS 

#### palettes.db (Model)
This is the database which stores all the information about users and their palettes. It has two tables: users and combos. The users table contains an id for the user which is autoincremented, a username and a hashed password. The combos table stores the base_color, complementary, analogous, and triadic colors along with the timestamp of when the palette was saved. Each palette has a user_id (foreign key) and an id (primary key).

#### requirements.txt
requirements.txt lists the libraries that need to be installed in order to run this application

#### Design Decisions 
The homepage includes a Get started button, guiding the user towards the main feature of the app, which makes navigation more intuitive. The navbar increases accesiblity as the user can easily navigate across pages. On the generate palettes page, using two tabs on a single page enables the user to use both features of the app on a single page, offering a better user experience. The upload an image option allows users to get results from images increasing precision and flexibility. There is also a color wheel section that allows learn about the uses of the combinations found. The generate palette page has a link to this section enhancing visibility and convenience. Users can save palettes for later use, offering control and are only accessible to logged in users providing privacy. Some other design decisions include enhancing appearance such as by adding rounded edges, columns, grids, margins, padding and other CSS and bootstrap classes.






