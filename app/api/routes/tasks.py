from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskUpdate
from app.services import task_service

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_task(db: Session, task_id: int, user_id: int) -> Task:
    task = task_service.get_task(db, task_id, user_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: DbSession, user: CurrentUser) -> Task:
    return task_service.create_task(db, data, user.id)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    db: DbSession,
    user: CurrentUser,
    completed: bool | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    return task_service.list_tasks(db, user.id, completed=completed, priority=priority)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: DbSession, user: CurrentUser) -> Task:
    return get_owned_task(db, task_id, user.id)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: DbSession, user: CurrentUser) -> Task:
    task = get_owned_task(db, task_id, user.id)
    return task_service.update_task(db, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: DbSession, user: CurrentUser) -> None:
    task = get_owned_task(db, task_id, user.id)
    task_service.delete_task(db, task)
