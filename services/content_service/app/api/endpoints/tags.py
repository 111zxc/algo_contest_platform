from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.tag import TagCreate, TagRead
from app.services.tag import create_tag, delete_tag, get_tag, get_tags, update_tag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=TagRead)
def create_tag_endpoint(
    tag_in: TagCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Создает новый тег admin only
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create tags"
        )

    tag = create_tag(db, tag_in)
    return tag


@router.get("/{tag_id}", response_model=TagRead)
def read_tag_endpoint(tag_id: str, db: Session = Depends(get_db)):
    """
    Возвращает тег по его id
    404, если тега не существует
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    return tag


@router.put("/{tag_id}", response_model=TagRead)
def update_tag_endpoint(
    tag_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет тег по его id admin only
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update tags"
        )

    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    tag = update_tag(db, tag, update_data)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag_endpoint(
    tag_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет тег по его id adminonly
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete tags"
        )
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    delete_tag(db, tag)
    return


@router.get("/", response_model=list[TagRead])
def list_tags_endpoint(db: Session = Depends(get_db)):
    """
    Возвращает list[TagRead] всех тэгов без авторизации
    """
    tags = get_tags(db)
    return tags
