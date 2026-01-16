from flask import Flask, request, redirect, render_template_string
import sqlite3, os

app = Flask(__name__)

DB_PATH = "swarg.db"

# ---------- DATABASE ----------
def get_db():
    con = sqlite3.connect(DB_PATH)
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
body{font-family:Arial;background:#f0f2f5;margin:0}
header{background:#1877f2;color:white;padding:15px;text-align:center;font-size:24px}
.card{background:white;max-width:350px;margin:40px auto;padding:20px;border-radius:8px}
label{font-weight:bold}
input,button{width:100%;padding:10px;margin:8px 0}
button{background:#1877f2;color:white;border:none;font-size:16px}
.error{color:red;text-align:center}
a{text-decoration:none;color:#1877f2}
</style>
</head>
<body>
<header>SWARG</header>
{{body}}
</body>
</html>
"""

def page(body):
    return render_template_string(BASE, body=body)

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()

        if not u or not p:
            error = "Username and password required"
        else:
            db = get_db()
            row = db.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (u,p)
            ).fetchone()
            if row:
                return f"<h2 style='text-align:center'>Welcome {u} 🎉</h2>"
            else:
                error = "Account not found"

    return page(f"""
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
        <a href="/register">Create new account</a>
    </p>
    </div>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    error = ""
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()

        if not u or not p:
            error = "All fields required"
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users(username,password) VALUES(?,?)",
                        (u,p)
                    )
                return redirect("/")
            except sqlite3.IntegrityError:
                error = "Username already exists"

    return page(f"""
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
    """)

# ---------- RUN ----------
app.run(host="0.0.0.0", port=5000)
