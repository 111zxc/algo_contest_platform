from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import authorize, get_current_user
from app.core.database import get_db
from app.models.contest import Contest
from app.schemas.contest import ContestCreate, ContestJoin, ContestRead
from app.schemas.problem import ProblemRead
from app.schemas.user import UserRead
from app.services.contest import (
    add_user_to_contest_by_username,
    create_contest,
    delete_contest,
    get_contest,
    join_public_contest,
    list_contest_participants,
    list_contest_tasks,
    list_owner_contests,
    list_public_contests,
    list_user_contests,
    update_contest,
)

router = APIRouter(prefix="/contests", tags=["contests"])


def get_contest_or_404(contest_id: UUID, db=Depends(get_db)):
    c = get_contest(db, str(contest_id))
    if not c:
        raise HTTPException(status_code=404, detail="Contest not found")
    return c


@router.get(
    "/my_participate",
    response_model=list[ContestRead],
    status_code=status.HTTP_200_OK,
)
def list_my_participate_contests_endpoint(
    user_claims: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    return list_user_contests(db, user_claims["sub"])


@router.post("/", response_model=ContestRead, status_code=status.HTTP_201_CREATED)
def create_contest_endpoint(
    data: ContestCreate,
    db=Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    return create_contest(db, data, user_claims["sub"])


@router.get("/my", response_model=list[ContestRead])
def list_my_contests_endpoint(
    db=Depends(get_db), user_claims: dict = Depends(get_current_user)
):
    user_id = user_claims["sub"]
    return list_owner_contests(db, user_id)


@router.get("/{contest_id}", response_model=ContestRead)
def read_contest_endpoint(contest: Contest = Depends(get_contest_or_404)):
    return contest


@router.put("/{contest_id}", response_model=ContestRead)
@authorize(required_role="admin", owner_param="contest", owner_field="created_by")
def update_contest_endpoint(
    update_data: dict,
    contest: Contest = Depends(get_contest_or_404),
    db=Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    return update_contest(db, contest, update_data)


@router.delete("/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="contest", owner_field="created_by")
def delete_contest_endpoint(
    contest: Contest = Depends(get_contest_or_404),
    db=Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    delete_contest(db, contest)


@router.get("/", response_model=list[ContestRead])
def list_contests_endpoint(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db=Depends(get_db),
):
    return list_public_contests(db, offset, limit)


@router.post("/{contest_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def join_contest_endpoint(
    contest_id: str,
    db=Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    join_public_contest(db, contest_id, user_claims["sub"])


@router.post("/{contest_id}/participants", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="contest", owner_field="created_by")
def add_participant_endpoint(
    payload: ContestJoin,
    contest=Depends(get_contest_or_404),
    db=Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    add_user_to_contest_by_username(
        db, str(contest.id), payload.username
    )


@router.get(
    "/{contest_id}/participants",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
def list_participants_endpoint(
    contest=Depends(get_contest_or_404),
    db=Depends(get_db),
):
    return list_contest_participants(db, str(contest.id))


@router.get(
    "/{contest_id}/tasks",
    response_model=list[ProblemRead],
    status_code=status.HTTP_200_OK,
)
def list_tasks_endpoint(
    contest_id: str,
    db=Depends(get_db),
):
    return list_contest_tasks(db, str(contest_id))
