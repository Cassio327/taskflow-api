from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskPriority, TaskUpdate


def create_task(db: Session, data: TaskCreate, user_id: int) -> Task:
    task = Task(**data.model_dump(), user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    user_id: int,
    completed: bool | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    query = select(Task).where(Task.user_id == user_id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority.value)
    query = query.order_by(Task.id)
    return list(db.scalars(query).all())


def get_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
