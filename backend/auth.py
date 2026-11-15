"""Minimal email/password auth: SQLite users, PBKDF2 password hashes, HMAC-signed bearer tokens."""
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, time
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "users.db")
_sf = os.path.join(HERE, ".secret")
if os.environ.get("TALENTRANK_SECRET"): SECRET = os.environ["TALENTRANK_SECRET"].encode()
else:
    if not os.path.exists(_sf): open(_sf, "w").write(secrets.token_hex(32))
    SECRET = open(_sf).read().encode()
TTL = 60 * 60 * 24 * 7  # 7 days

def _db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY, name TEXT, salt TEXT, pw TEXT)")
    return c

def _hash(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()

def _token(email, name):
    body = base64.urlsafe_b64encode(json.dumps({"e": email, "n": name, "x": int(time.time()) + TTL}).encode()).decode()
    return body + "." + hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()

def current_user(authorization: str = Header(default="")):
    try:
        body, sig = authorization.removeprefix("Bearer ").strip().split(".")
        if not hmac.compare_digest(sig, hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()): raise ValueError
        d = json.loads(base64.urlsafe_b64decode(body))
        if d["x"] < time.time(): raise ValueError
        return {"email": d["e"], "name": d["n"]}
    except Exception:
        raise HTTPException(401, "Please sign in to continue.")

class Reg(BaseModel): name: str; email: str; password: str
class Login(BaseModel): email: str; password: str

router = APIRouter(prefix="/api")

@router.post("/register")
def register(r: Reg):
    email, name = r.email.strip().lower(), r.name.strip()
    if not name: raise HTTPException(400, "Enter your name.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): raise HTTPException(400, "Enter a valid email address.")
    if len(r.password) < 8: raise HTTPException(400, "Use a password with at least 8 characters.")
    salt = secrets.token_hex(16)
    try:
        with _db() as c: c.execute("INSERT INTO users VALUES(?,?,?,?)", (email, name, salt, _hash(r.password, salt)))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with this email already exists. Sign in instead.")
    return {"token": _token(email, name), "name": name, "email": email}

@router.post("/login")
def login(r: Login):
    email = r.email.strip().lower()
    row = _db().execute("SELECT name,salt,pw FROM users WHERE email=?", (email,)).fetchone()
    if not row or not hmac.compare_digest(row[2], _hash(r.password, row[1])):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": _token(email, row[0]), "name": row[0], "email": email}

@router.get("/me")
def me(u=Depends(current_user)): return u
