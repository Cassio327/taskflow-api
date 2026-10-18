from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "TaskFlow API online"}


@router.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}
