from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user, get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user import create_user, delete_user, get_user, get_users, update_user

router = APIRouter(prefix="/users", tags=["users"])


def get_user_or_404(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return user


@router.get("/whoami", response_model=UserRead)
def whoami_endpoint(
    db: Session = Depends(get_db), user_claims: dict = Depends(get_current_user)
):
    """
    Возвращает информацию о текущем пользователе, используя данные из авторизационного токена.

    Эндпоинт не требует передачи идентификатора пользователя явно,
    поскольку он извлекается из токена (поле 'sub').

    Returns:
        UserRead: Информация о пользователе, полученная из базы данных.

    Raises:
        HTTPException 401: Если токен не содержит 'sub'.
        HTTPException 404: Если пользователь не найден в базе.
    """
    keycloak_id = user_claims.get("sub")
    if not keycloak_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    return get_user_or_404(keycloak_id, db)


@router.get("/amiadmin", response_model=dict)
def am_i_admin_endpoint(user_claims: dict = Depends(get_current_user)):
    """
    Определяет, является ли текущий пользователь администратором.

    Эндпоинт анализирует данные из авторизационного токена и проверяет наличие
    роли "admin" в realm_access.roles. Если роль присутствует, то возвращается is_admin = True, иначе False.

    Returns:
        dict: {
            "is_admin": bool,  // True, если роль "admin" присутствует; иначе False.
            "roles": list      // Список ролей, полученных из токена.
        }
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    is_admin = "admin" in roles
    return {"is_admin": is_admin, "roles": roles}


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
    return get_user_or_404(keycloak_id, db)


@router.put("/{keycloak_id}", response_model=UserRead)
@authorize(required_role="admin", owner_param="keycloak_id")
def update_user_endpoint(
    keycloak_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    updated_user = update_user(db, user, update_data)
    return updated_user


@router.delete("/{keycloak_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin")
def delete_user_endpoint(
    keycloak_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
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
