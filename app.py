from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "blogging-platform-secret-key"


def get_db():
    conn = sqlite3.connect("blog.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    init_db()


# HOME
@app.route("/")
def home():

    conn = get_db()

    blogs = conn.execute("""
        SELECT blogs.*, users.username
        FROM blogs
        LEFT JOIN users ON blogs.author_id = users.id
        ORDER BY blogs.created_at DESC
    """).fetchall()

    conn.close()

    return render_template("index.html", blogs=blogs)


# VIEW BLOG
@app.route("/blog/<int:blog_id>")
def view_blog(blog_id):

    conn = get_db()

    blog = conn.execute("""
        SELECT blogs.*, users.username
        FROM blogs
        LEFT JOIN users ON blogs.author_id = users.id
        WHERE blogs.id = ?
    """, (blog_id,)).fetchone()

    conn.close()

    if blog is None:
        return "Blog not found!"

    return render_template("blog.html", blog=blog)


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            """, (username, email, password))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered!"

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password!"

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"]
    )


# CREATE BLOG
@app.route("/create-blog", methods=["GET", "POST"])
def create_blog():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        conn = get_db()

        conn.execute("""
            INSERT INTO blogs (title, content, author_id)
            VALUES (?, ?, ?)
        """, (title, content, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("create_blog.html")


# EDIT BLOG
@app.route("/edit-blog/<int:blog_id>", methods=["GET", "POST"])
def edit_blog(blog_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    blog = conn.execute(
        "SELECT * FROM blogs WHERE id = ? AND author_id = ?",
        (blog_id, session["user_id"])
    ).fetchone()

    if blog is None:
        conn.close()
        return "Blog not found or you are not authorized!"

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        conn.execute("""
            UPDATE blogs
            SET title = ?, content = ?
            WHERE id = ? AND author_id = ?
        """, (title, content, blog_id, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("view_blog", blog_id=blog_id))

    conn.close()

    return render_template("edit_blog.html", blog=blog)


# DELETE BLOG
@app.route("/delete-blog/<int:blog_id>")
def delete_blog(blog_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM blogs WHERE id = ? AND author_id = ?",
        (blog_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# RUN APPLICATION
if __name__ == "__main__":
    init_db()
    app.run()
