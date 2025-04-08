from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user, delete_user, get_user, get_users, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
def create_user_endpoint(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Создает нового пользователя по keycloak-токену.
    """
    user_in.keycloak_id = user_claims.get("sub")
    user = create_user(db, user_in)
    return user


@router.get("/{keycloak_id}", response_model=UserRead)
def read_user_endpoint(keycloak_id: str, db: Session = Depends(get_db)):
    """
    Возвращает пользователя в виде schemas.user.UserRead по его keycloak_id.
    Возвращает 404, если пользователь не найден.
    """
    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/{keycloak_id}", response_model=UserRead)
def update_user_endpoint(
    keycloak_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет предосталвенные в JSON-body поля пользователея по его keycloak_id,
    .. возвращает обновленную информацию в виде schemas.user.UserRead
    403, если не сам пользователь или не admin.
    404, если пользователь по keycloak_id не найден.
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.keycloak_id != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )

    user = update_user(db, user, update_data)
    return user


@router.delete("/{keycloak_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    keycloak_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет пользователя по его keycloak_id и возвращает 204.
    404, если пользователя не существует
    403, если авторизация не admin
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete users"
        )

    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    delete_user(db, user)
    return


@router.get("/", response_model=list[UserRead])
def list_users_endpoint(db: Session = Depends(get_db)):
    """
    Возвращает список всех пользователей.
    """
    users = get_users(db)
    return users
