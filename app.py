import os
import psycopg2
from flask import Flask, request, redirect, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "swarg_secret")

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

# ---------- INIT DATABASE ----------
with db() as con:
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        bio TEXT DEFAULT ''
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id SERIAL PRIMARY KEY,
        username TEXT,
        content TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes(
        username TEXT,
        post_id INTEGER
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS follows(
        follower TEXT,
        following TEXT
    );
    """)
    con.commit()

# ---------- BASE HTML ----------
BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Swarg</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;font-family:Arial;background:#f0f2f5}
header{background:#1877f2;color:white;padding:12px;text-align:center;font-size:22px}
.card{background:white;margin:10px;padding:14px;border-radius:8px}
input,textarea,button{width:100%;padding:12px;margin-top:8px;font-size:16px}
button{background:#1877f2;color:white;border:none;border-radius:6px}
nav{position:fixed;bottom:0;width:100%;background:#fff;border-top:1px solid #ccc;display:flex}
nav a{flex:1;text-align:center;padding:10px;text-decoration:none;color:#1877f2;font-weight:bold}
.like{color:red;font-weight:bold}
.avatar{
width:60px;height:60px;border-radius:50%;
background:#1877f2;color:white;
display:flex;align-items:center;justify-content:center;
font-size:24px;margin:auto
}
</style>
</head>
<body>
<header>SWARG</header>
<div style="padding-bottom:70px">
{{ body | safe }}
</div>
</body>
</html>
"""

NAV = """
<nav>
<a href="/home">Home</a>
<a href="/search">Search</a>
<a href="/profile">Profile</a>
<a href="/logout">Logout</a>
</nav>
"""

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    msg=""
    if request.method=="POST":
        with db() as con:
            cur=con.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (request.form["username"],request.form["password"])
            )
            if cur.fetchone():
                session["user"]=request.form["username"]
                return redirect("/home")
        msg="Wrong login"
    return render_template_string(BASE, body=f"""
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Login</button>
    </form>
    <p style="color:red">{msg}</p>
    <a href="/register">Create account</a>
    </div>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    msg=""
    if request.method=="POST":
        try:
            with db() as con:
                cur=con.cursor()
                cur.execute(
                    "INSERT INTO users(username,password) VALUES(%s,%s)",
                    (request.form["username"],request.form["password"])
                )
                con.commit()
            return redirect("/")
        except:
            msg="Username exists"
    return render_template_string(BASE, body=f"""
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Create</button>
    </form>
    <p style="color:red">{msg}</p>
    </div>
    """)

# ---------- HOME / FEED ----------
@app.route("/home", methods=["GET","POST"])
def home():
    if "user" not in session: return redirect("/")
    u=session["user"]

    if request.method=="POST":
        with db() as con:
            cur=con.cursor()
            cur.execute(
                "INSERT INTO posts(username,content) VALUES(%s,%s)",
                (u,request.form["post"])
            )
            con.commit()

    feed=""
    with db() as con:
        cur=con.cursor()
        cur.execute("SELECT id,username,content FROM posts ORDER BY id DESC")
        posts=cur.fetchall()
        for p in posts:
            cur.execute(
                "SELECT COUNT(*) FROM likes WHERE post_id=%s",(p[0],)
            )
            likes=cur.fetchone()[0]
            feed+=f"""
            <div class="card">
            <b>{p[1]}</b><br>{p[2]}<br>
            <a href="/like/{p[0]}" class="like">❤ {likes}</a>
            </div>
            """

    return render_template_string(BASE, body=f"""
    <div class="card">
    <form method="post">
    <textarea name="post" placeholder="What's on your mind?" required></textarea>
    <button>Post</button>
    </form>
    </div>
    {feed}
    {NAV}
    """)

# ---------- LIKE ----------
@app.route("/like/<int:pid>")
def like(pid):
    if "user" not in session: return redirect("/")
    with db() as con:
        cur=con.cursor()
        cur.execute(
            "INSERT INTO likes(username,post_id) VALUES(%s,%s)",
            (session["user"],pid)
        )
        con.commit()
    return redirect("/home")

# ---------- SEARCH ----------
@app.route("/search")
def search():
    if "user" not in session: return redirect("/")
    q=request.args.get("q","")
    res=""
    with db() as con:
        cur=con.cursor()
        cur.execute(
            "SELECT username FROM users WHERE username LIKE %s",
            ("%"+q+"%",)
        )
        for u in cur.fetchall():
            res+=f"<div class='card'><a href='/user/{u[0]}'>{u[0]}</a></div>"
    return render_template_string(BASE, body=f"""
    <div class="card">
    <form>
    <input name="q" placeholder="Search user">
    <button>Search</button>
    </form>
    </div>
    {res}
    {NAV}
    """)

# ---------- USER PROFILE ----------
@app.route("/user/<name>")
def user(name):
    with db() as con:
        cur=con.cursor()
        cur.execute("SELECT bio FROM users WHERE username=%s",(name,))
        bio=cur.fetchone()[0]
    initials=name[:2].upper()
    return render_template_string(BASE, body=f"""
    <div class="card">
    <div class="avatar">{initials}</div>
    <h3 style="text-align:center">{name}</h3>
    <p>{bio}</p>
    </div>
    {NAV}
    """)

# ---------- OWN PROFILE ----------
@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user" not in session: return redirect("/")
    u=session["user"]
    if request.method=="POST":
        with db() as con:
            cur=con.cursor()
            cur.execute(
                "UPDATE users SET bio=%s WHERE username=%s",
                (request.form["bio"],u)
            )
            con.commit()
    with db() as con:
        cur=con.cursor()
        cur.execute("SELECT bio FROM users WHERE username=%s",(u,))
        bio=cur.fetchone()[0]
    initials=u[:2].upper()
    return render_template_string(BASE, body=f"""
    <div class="card">
    <div class="avatar">{initials}</div>
    <h3 style="text-align:center">{u}</h3>
    <form method="post">
    <textarea name="bio" placeholder="About you">{bio}</textarea>
    <button>Save</button>
    </form>
    </div>
    {NAV}
    """)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
