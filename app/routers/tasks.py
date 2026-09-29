import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.database import get_db, get_redis
from app.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

CACHE_TTL_SECONDS = 30


def _cache_key(user_id: int, status_filter: Optional[str], skip: int, limit: int) -> str:
    return f"tasks:{user_id}:{status_filter}:{skip}:{limit}"


def _invalidate_user_cache(redis_client, user_id: int) -> None:
    for key in redis_client.scan_iter(f"tasks:{user_id}:*"):
        redis_client.delete(key)


@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    db_task = crud.create_task(db, task, owner_id=current_user.id)
    _invalidate_user_cache(redis_client, current_user.id)
    return db_task


@router.get("/", response_model=list[schemas.TaskOut])
def list_tasks(
    status_filter: Optional[models.TaskStatus] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    key = _cache_key(current_user.id, status_filter, skip, limit)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    tasks = crud.get_tasks(db, current_user.id, status_filter, skip, limit)
    result = [schemas.TaskOut.model_validate(t).model_dump(mode="json") for t in tasks]
    redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(result))
    return result


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = crud.update_task(db, task, task_update)
    _invalidate_user_cache(redis_client, current_user.id)
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, task)
    _invalidate_user_cache(redis_client, current_user.id)
