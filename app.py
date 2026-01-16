from flask import Flask, request, redirect
from flask import render_template_string
import sqlite3

app = Flask(__name__)
DB = "swarg.db"

# ---------- DATABASE ----------
def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

with get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
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
.card{background:white;max-width:360px;margin:40px auto;padding:20px;border-radius:8px}
label{display:block;margin-top:10px;font-weight:bold}
input,button{width:100%;padding:10px;margin-top:5px}
button{background:#1877f2;color:white;border:none;font-size:16px;margin-top:15px}
.error{color:red;text-align:center;margin-top:10px}
a{color:#1877f2;text-decoration:none}
</style>
</head>
<body>
<header>SWARG</header>
{{ content }}
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

        if not u or not p:
            error="Username and password required"
        else:
            db=get_db()
            r=db.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (u,p)
            ).fetchone()
            if r:
                return f"<h2 style='text-align:center'>Welcome {u} 🎉</h2>"
            else:
                error="Account not found"

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
        <p style="text-align:center;margin-top:15px">
            <a href="/register">Create new account</a>
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

        if not u or not p:
            error="All fields required"
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users(username,password) VALUES(?,?)",
                        (u,p)
                    )
                return redirect("/")
            except sqlite3.IntegrityError:
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
        <p style="text-align:center;margin-top:15px">
            <a href="/">Back to login</a>
        </p>
    </div>
    """
    return render_template_string(BASE, content=html)

# ---------- RUN ----------
app.run(host="0.0.0.0", port=5000)
