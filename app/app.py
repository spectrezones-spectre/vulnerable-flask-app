from __future__ import annotations

import os
import sqlite3
from functools import wraps
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "lab.db")
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config.update(SECRET_KEY="local-training-only-change-me", DATABASE=DB_PATH)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Any = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return get_db().execute(sql, params).fetchall()


def fetch_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return get_db().execute(sql, params).fetchone()


def get_current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return fetch_one(
        "SELECT u.*, r.name AS role_name, r.description AS role_description "
        "FROM users u JOIN roles r ON r.id = u.role_id WHERE u.id = ?",
        (user_id,),
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            flash("Connectez-vous pour accéder à cette zone.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_context():
    return {"current_user": get_current_user()}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "") # alice' OR 1=1--
        password = request.form.get("password", "")
        # VULNERABLE — unsafe SQL interpolation, shown for comparison with /login-safe.
        sql = (
            "SELECT u.*, r.name AS role_name, r.description AS role_description "
            "FROM users u JOIN roles r ON r.id = u.role_id "
            
            f"WHERE u.username = '{username}' AND u.password = '{password}'"
        )
        try:
            rows = fetch_all(sql)
        except sqlite3.Error as exc:
            error = f"Erreur SQLite observée : {exc}"
            rows = []
        if rows:
            session.clear()
            session["user_id"] = rows[0]["id"]
            flash("Connexion réussie via le point d’entrée vulnérable.", "success")
            return redirect(url_for("dashboard"))
        if error is None:
            error = "Identifiants incorrects. Vérifiez le statut de réponse et le contenu renvoyé."
    return render_template("login.html", error=error, safe=False, endpoint="POST /login")


@app.route("/login-safe", methods=["GET", "POST"])
def login_safe():
    error = None
    if request.method == "POST":
        row = fetch_one(
            "SELECT u.*, r.name AS role_name, r.description AS role_description "
            "FROM users u JOIN roles r ON r.id = u.role_id "
            
            "WHERE u.username = ? AND u.password = ?",
            (request.form.get("username", ""), request.form.get("password", "")),
        )
        if row:
            session.clear()
            session["user_id"] = row["id"]
            flash("Connexion réussie avec une requête paramétrée.", "success")
            return redirect(url_for("dashboard"))
        error = "Identifiants refusés par la version sécurisée."
    return render_template("login.html", error=error, safe=True, endpoint="POST /login-safe")


@app.route("/logout")
def logout():
    session.clear()
    flash("Session locale terminée.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    products = fetch_all("SELECT * FROM products ORDER BY id")
    return render_template("dashboard.html", products=products)


@app.route("/search")
def search():
    term = request.args.get("q", "")
    rows: list[sqlite3.Row] = []
    error = None
    # Unsafe on purpose: four visible columns make UNION behavior observable.
    sql = (
        "SELECT id, name, category, price FROM products "
        f"WHERE name LIKE '%{term}%' OR category LIKE '%{term}%'"
    )
    try:
        rows = fetch_all(sql)
    except sqlite3.Error as exc:
        error = f"Erreur SQLite : {exc}"
    return render_template(
        "search.html", rows=rows, term=term, error=error, safe=False,
        endpoint="GET /search?q=", sql_shape="SELECT id, name, category, price FROM products WHERE ...",
    )


@app.route("/search-safe")
def search_safe():
    term = request.args.get("q", "")
    rows = fetch_all(
        "SELECT id, name, category, price FROM products "
        "WHERE name LIKE ? OR category LIKE ?",
        (f"%{term}%", f"%{term}%"),
    )
    return render_template(
        "search.html", rows=rows, term=term, error=None, safe=True,
        endpoint="GET /search-safe?q=", sql_shape="SELECT ... WHERE name LIKE ? OR category LIKE ?",
    )


@app.route("/search-post", methods=["GET", "POST"])
def search_post():
    term = request.form.get("q", "") if request.method == "POST" else ""
    rows: list[sqlite3.Row] = []
    error = None
    if request.method == "POST":
        # Unsafe on purpose: mirrors the GET search through an HTTP form body.
        sql = f"SELECT id, name, category, price FROM products WHERE name LIKE '%{term}%'"
        try:
            rows = fetch_all(sql)
        except sqlite3.Error as exc:
            error = f"Erreur SQLite : {exc}"
    return render_template("search_post.html", rows=rows, term=term, error=error)


@app.route("/product")
def product():
    product_id = request.args.get("id", "")
    rows: list[sqlite3.Row] = []
    error = None
    try:
        # Unsafe on purpose: the numeric-looking id parameter is concatenated raw.
        rows = fetch_all(
            f"SELECT id, name, description, category, price, stock FROM products WHERE id = {product_id}"
        )
    except sqlite3.Error as exc:
        error = f"Erreur de syntaxe observée : {exc}"
    return render_template("product.html", rows=rows, product_id=product_id, error=error, safe=False)


@app.route("/product-safe")
def product_safe():
    product_id = request.args.get("id", "")
    rows: list[sqlite3.Row] = []
    error = None
    try:
        rows = fetch_all(
            "SELECT id, name, description, category, price, stock FROM products WHERE id = ?",
            (product_id,),
        )
    except sqlite3.Error as exc:
        error = f"Erreur inattendue : {exc}"
    return render_template("product.html", rows=rows, product_id=product_id, error=error, safe=True)


@app.route("/admin")
@login_required
def admin():
    # Reference: authorization is decided server-side from the session.
    if get_current_user()["role_name"] != "admin":
        return render_template("denied.html", reason="Votre rôle serveur n’est pas admin."), 403
    users = fetch_all("SELECT u.id, u.username, u.email, r.name AS role_name FROM users u JOIN roles r ON r.id=u.role_id")
    return render_template("admin.html", users=users, vulnerable=False)


@app.route("/admin-vulnerable")
@login_required
def admin_vulnerable():
    # Unsafe on purpose: a client-controlled query parameter decides authorization.
    requested_role = request.args.get("as_role", "")
    if requested_role != "admin":
        return render_template("denied.html", reason="Le paramètre as_role n’a pas la valeur attendue."), 403
    users = fetch_all("SELECT u.id, u.username, u.email, r.name AS role_name FROM users u JOIN roles r ON r.id=u.role_id")
    return render_template("admin.html", users=users, vulnerable=True)


@app.route("/health")
def health():
    required = {"roles", "users", "products", "audit_log"}
    tables = {row["name"] for row in fetch_all("SELECT name FROM sqlite_master WHERE type='table'")}
    return {"status": "ok", "database": os.path.exists(app.config["DATABASE"]), "schema_complete": required.issubset(tables)}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
