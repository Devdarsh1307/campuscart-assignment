"""CampusCart API - stateless; all state lives in the external database."""
import os
import socket

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text

APP_VERSION = os.getenv("APP_VERSION", "dev")


def read_secret(name, default=None):
    """Prefer a mounted secret file (/run/secrets/<name>), fall back to env var."""
    path = os.getenv(name + "_FILE", "/run/secrets/" + name.lower())
    if os.path.isfile(path):
        with open(path) as fh:
            return fh.read().strip()
    return os.getenv(name, default)


def database_url():
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host = os.getenv("DB_HOST")
    if not host:
        return "sqlite:///:memory:"
    user = os.getenv("DB_USER", "campuscart")
    pwd = read_secret("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "campuscart")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"


def create_app(db_url=None):
    app = Flask(__name__)
    url = db_url or database_url()
    kwargs = {}
    if url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        kwargs = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    engine = create_engine(url, pool_pre_ping=True, **kwargs)
    app.engine = engine
    id_col = "INTEGER PRIMARY KEY AUTOINCREMENT" if url.startswith("sqlite") else "SERIAL PRIMARY KEY"

    def init_db():
        import time
        for attempt in range(10):  # DB may be starting, or replicas race to create the table
            try:
                with engine.begin() as c:
                    c.execute(text(
                        f"CREATE TABLE IF NOT EXISTS orders (id {id_col}, item TEXT NOT NULL, qty INTEGER NOT NULL)"))
                return
            except Exception:
                if attempt == 9:
                    raise
                time.sleep(2)

    app.init_db = init_db

    @app.get("/health")
    def health():
        if os.getenv("FAIL_HEALTH") == "1":  # simulates a faulty release (v1.1.0)
            return jsonify(status="unhealthy", version=APP_VERSION), 500
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
        except Exception:
            return jsonify(status="db_unavailable", version=APP_VERSION), 503
        return jsonify(status="ok", version=APP_VERSION, instance=socket.gethostname())

    @app.get("/products")
    def products():
        return jsonify([{"id": 1, "name": "Notebook", "price": 60},
                        {"id": 2, "name": "Pen pack", "price": 40}])

    @app.post("/orders")
    def create_order():
        data = request.get_json(silent=True) or {}
        if not data.get("item") or int(data.get("qty", 0)) < 1:
            return jsonify(error="item and qty>=1 required"), 400
        with engine.begin() as c:
            c.execute(text("INSERT INTO orders (item, qty) VALUES (:i, :q)"),
                      {"i": data["item"], "q": int(data["qty"])})
        return jsonify(status="created"), 201

    @app.get("/orders")
    def list_orders():
        with engine.connect() as c:
            rows = c.execute(text("SELECT id, item, qty FROM orders ORDER BY id")).all()
        return jsonify([{"id": r[0], "item": r[1], "qty": r[2]} for r in rows])

    return app


def build():
    app = create_app()
    app.init_db()
    return app


_app = None


def __getattr__(name):  # lazy WSGI object: gunicorn app:app
    global _app
    if name == "app":
        if _app is None:
            _app = build()
        return _app
    raise AttributeError(name)
