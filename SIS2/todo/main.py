"""To-Do / Task Tracker API (SIS #1).

REST + JSON, JWT auth, SQLAlchemy (SQLite by default, PostgreSQL via DATABASE_URL).
"""
import datetime as dt
import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from typing import Literal, Optional

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (DateTime, ForeignKey, Index, String, Text,
                        UniqueConstraint, create_engine, func, select)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            sessionmaker)

# ---------------------------------------------------------------- config
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_TTL_MIN = int(os.getenv("JWT_TTL_MIN", "60"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# ---------------------------------------------------------------- models
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), default="todo")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    due_date: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), default=None)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_tasks_user", "user_id"),
        Index("idx_tasks_user_status", "user_id", "status"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_tasks_user_idem"),
    )


# ---------------------------------------------------------------- schemas
Status = Literal["todo", "in_progress", "done"]
Priority = Literal["low", "medium", "high"]


class Credentials(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: Status = "todo"
    priority: Priority = "medium"
    due_date: Optional[dt.datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due_date: Optional[dt.datetime] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[dt.datetime]
    created_at: dt.datetime
    updated_at: dt.datetime


class TaskList(BaseModel):
    items: list[TaskOut]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------- security
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": utcnow() + dt.timedelta(minutes=JWT_TTL_MIN)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


bearer = HTTPBearer(auto_error=False)


def get_db():
    with SessionLocal() as db:
        yield db


def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    try:
        user_id = int(jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "User not found")
    return user


# ---------------------------------------------------------------- app
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="To-Do / Task Tracker API", version="1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    # The design document specifies 400 (not FastAPI's default 422) for invalid input.
    errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
              for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": "Invalid input", "errors": errors})


# ---- auth
@app.post("/v1/auth/register", status_code=201)
def register(body: Credentials, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    return {"id": user.id, "email": user.email}


@app.post("/v1/auth/login")
def login(body: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


# ---- tasks
def get_own_task(db: Session, user: User, task_id: int) -> Task:
    # Filtering by user_id guarantees users only ever see their own tasks.
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@app.post("/v1/tasks", status_code=201, response_model=TaskOut)
def create_task(
    body: TaskCreate,
    response: Response,
    idempotency_key: Optional[str] = Header(default=None, max_length=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if idempotency_key:  # a retried request returns the original task instead of a duplicate
        existing = db.scalar(select(Task).where(
            Task.user_id == user.id, Task.idempotency_key == idempotency_key))
        if existing:
            response.status_code = 200
            return existing
    task = Task(user_id=user.id, idempotency_key=idempotency_key, **body.model_dump())
    db.add(task)
    db.commit()
    return task


@app.get("/v1/tasks", response_model=TaskList)
def list_tasks(
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    conds = [Task.user_id == user.id]
    if status:
        conds.append(Task.status == status)
    if priority:
        conds.append(Task.priority == priority)
    total = db.scalar(select(func.count()).select_from(Task).where(*conds))
    items = db.scalars(
        select(Task).where(*conds).order_by(Task.id.desc()).limit(limit).offset(offset)).all()
    return TaskList(items=items, total=total, limit=limit, offset=offset)


@app.get("/v1/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_own_task(db, user, task_id)


@app.patch("/v1/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = get_own_task(db, user, task_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("title") is None and "title" in changes:
        raise HTTPException(400, "title cannot be null")
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    return task


@app.delete("/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(get_own_task(db, user, task_id))
    db.commit()
    return Response(status_code=204)
