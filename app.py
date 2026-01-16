from flask import Flask, request, redirect, render_template_string
from werkzeug.utils import secure_filename
from markupsafe import Markup
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
DB = "swarg.db"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- DATABASE ----------
def db():
    return sqlite3.connect(DB, check_same_thread=False)

c = db().cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    dp TEXT,
    bio TEXT,
    school TEXT,
    work TEXT,
    city TEXT
)""")
c.execute("""CREATE TABLE IF NOT EXISTS posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    text TEXT,
    time TEXT
)""")
db().commit()

# ---------- BASE ----------
BASE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Swarg</title>
<style>
body{margin:0;font-family:Arial;background:#f0f2f5}
.header{background:#1877f2;color:white;padding:15px;text-align:center;font-size:24px}
.nav a{margin:10px;color:#1877f2;font-weight:bold;text-decoration:none}
.card{background:white;margin:15px;padding:15px;border-radius:12px}
img{width:55px;height:55px;border-radius:50%}
input,textarea{width:100%;padding:8px;margin:6px 0}
button{background:#1877f2;color:white;border:none;padding:8px 14px;border-radius:6px}
.small{color:gray;font-size:12px}
</style>
</head>
<body>
<div class="header">SWARG</div>
<div class="nav">{{ nav }}</div>
{{ body }}
</body>
</html>
"""

def page(nav, body):
    return render_template_string(
        BASE,
        nav=Markup(nav),
        body=Markup(body)
    )

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        cur=db().cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if cur.fetchone():
            return redirect(f"/feed/{u}")

    return page("", """
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="password" type="password" placeholder="Password">
    <button>Login</button>
    </form>
    <a href="/register">Create account</a>
    </div>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        try:
            db().cursor().execute(
                "INSERT INTO users VALUES(?,?,?,?,?,?,?)",
                (request.form["username"], request.form["password"],
                 "/static/default.png","","","","")
            )
            db().commit()
            return redirect("/")
        except:
            pass

    return page("", """
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    <input name="username" placeholder="Username">
    <input name="password" placeholder="Password">
    <button>Register</button>
    </form>
    </div>
    """)

# ---------- FEED ----------
@app.route("/feed/<u>", methods=["GET","POST"])
def feed(u):
    if request.method=="POST":
        db().cursor().execute(
            "INSERT INTO posts(username,text,time) VALUES(?,?,?)",
            (u, request.form["text"], datetime.now().strftime("%d %b %H:%M"))
        )
        db().commit()

    cur=db().cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts=cur.fetchall()

    out=""
    for _,user,text,time in posts:
        cur.execute("SELECT dp FROM users WHERE username=?", (user,))
        dp=cur.fetchone()[0]
        out+=f"""
        <div class="card">
        <img src="{dp}">
        <b>@{user}</b>
        <div class="small">{time}</div>
        <p>{text}</p>
        </div>
        """

    nav=f'<a href="/feed/{u}">Feed</a><a href="/search/{u}">Search</a><a href="/profile/{u}">Profile</a><a href="/edit/{u}">Edit</a><a href="/">Logout</a>'
    return page(nav, f"""
    <div class="card">
    <form method="post">
    <textarea name="text" placeholder="What's on your mind?"></textarea>
    <button>Post</button>
    </form>
    </div>
    {out}
    """)

# ---------- SEARCH ----------
@app.route("/search/<u>")
def search(u):
    q=request.args.get("q","")
    cur=db().cursor()
    cur.execute("SELECT username,dp FROM users WHERE username LIKE ?", (f"%{q}%",))
    res=cur.fetchall()

    out=""
    for user,dp in res:
        out+=f'<div class="card"><img src="{dp}"> <a href="/profile/{user}">@{user}</a></div>'

    nav=f'<a href="/feed/{u}">Feed</a><a href="/search/{u}">Search</a><a href="/profile/{u}">Profile</a><a href="/edit/{u}">Edit</a><a href="/">Logout</a>'
    return page(nav, f"""
    <div class="card">
    <form>
    <input name="q" placeholder="Search username">
    <button>Search</button>
    </form>
    </div>
    {out}
    """)

# ---------- PROFILE ----------
@app.route("/profile/<u>")
def profile(u):
    cur=db().cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (u,))
    user=cur.fetchone()

    cur.execute("SELECT * FROM posts WHERE username=? ORDER BY id DESC", (u,))
    posts=cur.fetchall()

    out=""
    for _,_,text,time in posts:
        out+=f"<div class='card'><p>{text}</p><div class='small'>{time}</div></div>"

    nav=f'<a href="/feed/{u}">Feed</a><a href="/search/{u}">Search</a><a href="/profile/{u}">Profile</a><a href="/edit/{u}">Edit</a><a href="/">Logout</a>'
    return page(nav, f"""
    <div class="card">
    <img src="{user[2]}">
    <h3>@{u}</h3>
    <p>{user[3]}</p>
    <p><b>School:</b> {user[4]}</p>
    <p><b>Work:</b> {user[5]}</p>
    <p><b>City:</b> {user[6]}</p>
    </div>
    {out}
    """)

# ---------- EDIT PROFILE ----------
@app.route("/edit/<u>", methods=["GET","POST"])
def edit(u):
    if request.method=="POST":
        f=request.files.get("dp")
        if f and f.filename:
            name=secure_filename(f.filename)
            path=os.path.join(UPLOAD_FOLDER,name)
            f.save(path)
            db().cursor().execute("UPDATE users SET dp=? WHERE username=?", ("/"+path,u))

        db().cursor().execute(
            "UPDATE users SET bio=?,school=?,work=?,city=? WHERE username=?",
            (request.form["bio"],request.form["school"],
             request.form["work"],request.form["city"],u)
        )
        db().commit()
        return redirect(f"/profile/{u}")

    nav=f'<a href="/feed/{u}">Feed</a><a href="/search/{u}">Search</a><a href="/profile/{u}">Profile</a><a href="/edit/{u}">Edit</a><a href="/">Logout</a>'
    return page(nav, """
    <div class="card">
    <form method="post" enctype="multipart/form-data">
    Change DP:<input type="file" name="dp">
    Bio:<textarea name="bio"></textarea>
    School:<input name="school">
    Work:<input name="work">
    City:<input name="city">
    <button>Save</button>
    </form>
    </div>
    """)

app.run(host="0.0.0.0", port=5000)
