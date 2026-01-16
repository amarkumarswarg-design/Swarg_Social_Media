from flask import Flask, request, redirect, render_template_string, session
import sqlite3

app = Flask(__name__)
app.secret_key = "swarg_secret_key"
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
        password TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT
    )
    """)

# ---------- BASE TEMPLATE ----------
BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Swarg</title>
<style>
body{margin:0;font-family:Arial;background:#f0f2f5}
header{background:#1877f2;color:white;padding:15px;text-align:center;font-size:24px}
nav{background:white;padding:10px;text-align:center}
nav a{margin:0 10px;color:#1877f2;text-decoration:none;font-weight:bold}
.card{background:white;max-width:500px;margin:15px auto;padding:15px;border-radius:8px}
label{font-weight:bold}
input,textarea,button{width:100%;padding:10px;margin-top:8px}
button{background:#1877f2;color:white;border:none;font-size:16px}
.error{color:red;text-align:center}
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
    error=""
    if request.method=="POST":
        u=request.form.get("username","").strip()
        p=request.form.get("password","").strip()

        r=db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u,p)
        ).fetchone()

        if r:
            session["user"]=u
            return redirect("/home")
        else:
            error="Wrong username or password"

    html=f"""
    <div class="card">
    <h3>Login</h3>
    <form method="post">
        <label>Username</label>
        <input name="username" required>
        <label>Password</label>
        <input name="password" type="password" required>
        <button>Login</button>
    </form>
    <div class="error">{error}</div>
    <p style="text-align:center">
        <a href="/register">Create account</a>
    </p>
    </div>
    """
    return render_template_string(BASE, content=html)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    error=""
    if request.method=="POST":
        u=request.form.get("username","").strip()
        p=request.form.get("password","").strip()
        try:
            with db() as c:
                c.execute(
                    "INSERT INTO users(username,password) VALUES(?,?)",
                    (u,p)
                )
            return redirect("/")
        except:
            error="Username already exists"

    html=f"""
    <div class="card">
    <h3>Create Account</h3>
    <form method="post">
        <label>Username</label>
        <input name="username" required>
        <label>Password</label>
        <input name="password" type="password" required>
        <button>Register</button>
    </form>
    <div class="error">{error}</div>
    <p style="text-align:center">
        <a href="/">Back to login</a>
    </p>
    </div>
    """
    return render_template_string(BASE, content=html)

# ---------- HOME / FEED ----------
@app.route("/home", methods=["GET","POST"])
def home():
    if "user" not in session:
        return redirect("/")

    user=session["user"]

    if request.method=="POST":
        txt=request.form.get("post","").strip()
        if txt:
            with db() as c:
                c.execute(
                    "INSERT INTO posts(username,content) VALUES(?,?)",
                    (user,txt)
                )

    posts_html=""
    rows=db().execute(
        "SELECT * FROM posts ORDER BY id DESC"
    ).fetchall()

    for r in rows:
        posts_html+=f"""
        <div class="card">
            <b>{r['username']}</b><br>
            {r['content']}
        </div>
        """

    html=f"""
    <nav>
        <a href="/home">Home</a>
        <a href="/logout">Logout</a>
    </nav>

    <div class="card">
        <h3>Welcome {user} 🎉</h3>
        <form method="post">
            <textarea name="post" placeholder="What's on your mind?" required></textarea>
            <button>Post</button>
        </form>
    </div>

    {posts_html}
    """
    return render_template_string(BASE, content=html)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
app.run(host="0.0.0.0", port=5000)
