from typing import Optional
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password


# --- Users ---
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(email=user.email, hashed_password=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Tasks ---
def create_task(db: Session, task: schemas.TaskCreate, owner_id: int) -> models.Task:
    db_task = models.Task(**task.model_dump(), owner_id=owner_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session,
    owner_id: int,
    status_filter: Optional[models.TaskStatus] = None,
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Task).filter(models.Task.owner_id == owner_id)
    if status_filter:
        query = query.filter(models.Task.status == status_filter)
    return query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int, owner_id: int) -> Optional[models.Task]:
    return (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.owner_id == owner_id)
        .first()
    )


def update_task(db: Session, db_task: models.Task, task_update: schemas.TaskUpdate) -> models.Task:
    for field, value in task_update.model_dump(exclude_unset=True).items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: models.Task) -> None:
    db.delete(db_task)
    db.commit()
