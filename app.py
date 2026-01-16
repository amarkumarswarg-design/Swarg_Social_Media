from flask import Flask, request, redirect, render_template_string, session
import sqlite3

app = Flask(__name__)
app.secret_key = "swarg_free"
DB = "swarg.db"

# ---------- DATABASE ----------
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

with db() as c:
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        bio TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT
    )
    """)

# ---------- BASE ----------
BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Swarg</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;font-family:Arial;background:#f0f2f5}
header{background:#1877f2;color:white;padding:12px;text-align:center;font-size:22px}
.card{background:white;margin:12px;padding:15px;border-radius:8px}
input,textarea,button{width:100%;padding:10px;margin-top:8px;font-size:16px}
button{background:#1877f2;color:white;border:none;border-radius:5px}
nav{position:fixed;bottom:0;width:100%;background:#fff;border-top:1px solid #ccc;display:flex}
nav a{flex:1;text-align:center;padding:10px;text-decoration:none;color:#1877f2;font-weight:bold}
.error{color:red;text-align:center}
.notice{color:#555;font-size:12px;text-align:center}
</style>
</head>
<body>
<header>SWARG</header>
{{ content | safe }}
</body>
</html>
"""

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    msg=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        r=db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u,p)
        ).fetchone()
        if r:
            session["user"]=u
            return redirect("/home")
        msg="Account not found (Free server restart resets data)"
    return render_template_string(BASE, content=f"""
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Login</button>
    </form>
    <div class="error">{msg}</div>
    <p class="notice">Free server = data may reset</p>
    <a href="/register">Create account</a>
    </div>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    msg=""
    if request.method=="POST":
        try:
            db().execute(
                "INSERT INTO users VALUES(?,?,?)",
                (request.form["username"], request.form["password"], "")
            )
            db().commit()
            return redirect("/")
        except:
            msg="Username exists"
    return render_template_string(BASE, content=f"""
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Create</button>
    </form>
    <div class="error">{msg}</div>
    </div>
    """)

# ---------- HOME ----------
@app.route("/home", methods=["GET","POST"])
def home():
    if "user" not in session:
        return redirect("/")
    user=session["user"]

    if request.method=="POST":
        db().execute(
            "INSERT INTO posts(username,content) VALUES(?,?)",
            (user, request.form["post"])
        )
        db().commit()

    posts=""
    for p in db().execute("SELECT * FROM posts ORDER BY id DESC"):
        posts+=f"<div class='card'><b>{p['username']}</b><br>{p['content']}</div>"

    return render_template_string(BASE, content=f"""
    <div class="card">
    <h3>Welcome {user}</h3>
    <form method="post">
    <textarea name="post" placeholder="What's on your mind?" required></textarea>
    <button>Post</button>
    </form>
    </div>
    {posts}
    <nav>
    <a href="/home">Home</a>
    <a href="/search">Search</a>
    <a href="/profile">Profile</a>
    <a href="/logout">Logout</a>
    </nav>
    """)

# ---------- SEARCH ----------
@app.route("/search")
def search():
    return render_template_string(BASE, content="""
    <div class="card">
    <h3>Search</h3>
    <p>Coming soon (free UI ready)</p>
    </div>
    """)

# ---------- PROFILE ----------
@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user" not in session:
        return redirect("/")
    u=session["user"]
    if request.method=="POST":
        db().execute(
            "UPDATE users SET bio=? WHERE username=?",
            (request.form["bio"],u)
        )
        db().commit()
    bio=db().execute(
        "SELECT bio FROM users WHERE username=?", (u,)
    ).fetchone()["bio"]
    return render_template_string(BASE, content=f"""
    <div class="card">
    <h3>{u}</h3>
    <form method="post">
    <textarea name="bio" placeholder="About you">{bio}</textarea>
    <button>Save</button>
    </form>
    </div>
    """)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=5000)
