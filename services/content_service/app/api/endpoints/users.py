from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserReadExtended
from app.services.user import (
    compute_user_rating,
    create_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_or_404(user_id: str, db: Session = Depends(get_db)) -> User:
    """
    Вспомогательная функция для @authorize, чтобы получать объект User через depends
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User can't be found"
        )
    return user


@router.get("/whoami", response_model=UserRead)
def whoami_endpoint(
    db: Session = Depends(get_db), user_claims: dict = Depends(get_current_user)
) -> UserRead:
    """
    Возвращает информацию о текущем пользователе, используя данные из авторизационного токена

    Args:
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе, извлечённые из токена авторизации

    Returns:
        UserRead - информация о пользователе, полученная из базы данных

    Raises:
        HTTPException 401 - если токен не содержит 'sub'
        HTTPException 404 - если пользователь не найден в базе
    """
    keycloak_id = user_claims.get("sub")
    if not keycloak_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    return get_user_or_404(keycloak_id, db)


@router.get("/amiadmin", response_model=dict)
def am_i_admin_endpoint(user_claims: dict = Depends(get_current_user)) -> dict:
    """
    Определяет, является ли текущий пользователь администратором и список его keycloak realm ролей

    Args:
        user_claims (dict): данные из авторизационного токена

    Returns:
        dict - {"is_admin": bool, "roles": list} где is_admin True, если у пользователя есть роль "admin", ..
            .. иначе False, roles – список ролей, полученных из токена
    """
    roles = user_claims.get("realm_access", {}).get("roles", [])
    is_admin = "admin" in roles
    return {"is_admin": is_admin, "roles": roles}


@router.get("/solved/{keycloak_id}", response_model=list[str])
def get_solved_problems_endpoint(
    keycloak_id: str, db: Session = Depends(get_db)
) -> list[str]:
    """
    Возвращает список идентификаторов задач, решённых пользователем с заданным keycloak_id

    Args:
        keycloak_id (str): идентификатор пользователя (Keycloak ID)
        db (Session): объект сессии БД

    Returns:
        list[str] - список идентификаторов решённых задач

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    solved_ids = [str(problem.id) for problem in user.solved_problems]
    return solved_ids


@router.post("/", response_model=UserRead)
def create_user_endpoint(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
) -> UserRead:
    """
    Создает нового пользователя по данным, полученным из авторизационного токена

    Args:
        user_in (UserCreate): объект с данными для создания пользователя
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        UserRead - созданный пользователь
    """
    user_in.keycloak_id = user_claims.get("sub")
    user = create_user(db, user_in)
    return user


@router.get("/{keycloak_id}", response_model=UserReadExtended)
def read_user_endpoint(
    keycloak_id: str, db: Session = Depends(get_db)
) -> UserReadExtended:
    """
    Возвращает пользователя с расширенной информацией (включая рейтинг) по его keycloak_id

    Args:
        keycloak_id (str): идентификатор пользователя (Keycloak ID)
        db (Session): объект сессии БД

    Returns:
        UserReadExtended - пользователь с дополнительным полем rating

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    user = get_user_or_404(keycloak_id, db)
    rating = compute_user_rating(db, user.keycloak_id)
    user_data = UserReadExtended.from_orm(user)
    user_data.rating = rating
    return user_data


@router.put("/{keycloak_id}", response_model=UserRead)
@authorize(required_role="admin", owner_param="keycloak_id")
def update_user_endpoint(
    keycloak_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
) -> UserRead:
    """
    Обновляет данные пользователя по его keycloak_id

    Args:
        keycloak_id (str): идентификатор пользователя (Keycloak ID) для обновления
        update_data (dict): словарь с данными для обновления
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        UserRead - обновленный пользователь

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    user = get_user_or_404(keycloak_id, db)
    updated_user = update_user(db, user, update_data)
    return updated_user


@router.delete("/{keycloak_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin")
def delete_user_endpoint(
    keycloak_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет пользователя по его keycloak_id

    Args:
        keycloak_id (str): идентификатор пользователя (Keycloak ID)
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        None - функция ничего не возвращает

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    user = get_user(db, keycloak_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    delete_user(db, user)
    return


@router.get("/", response_model=list[UserRead])
def list_users_endpoint(db: Session = Depends(get_db)) -> list[UserRead]:
    """
    Возвращает список всех пользователей

    Args:
        db (Session): объект сессии БД

    Returns:
        list[UserRead] - список пользователей
    """
    users = get_users(db)
    return users
