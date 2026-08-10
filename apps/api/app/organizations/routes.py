from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, require_permission
from app.auth.service import AuthenticatedUser
from app.db.session import get_db_session
from app.organizations import service
from app.organizations.schemas import (
    OrganizationModulesOut,
    OrganizationModulesPatch,
    OrganizationRolesOut,
    OrganizationSettingsOut,
    OrganizationSettingsPatch,
    OrganizationUserCreate,
    OrganizationUserOut,
    OrganizationUserPatch,
    OrganizationUserRolesPut,
    OrganizationUsersOut,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])

admin_manage = require_permission("admin.manage")


@router.get("/me/settings", response_model=OrganizationSettingsOut)
def get_my_organization_settings(
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationSettingsOut:
    return service.get_my_settings(session, user.organization_id)


@router.patch("/me/settings", response_model=OrganizationSettingsOut)
def patch_my_organization_settings(
    payload: OrganizationSettingsPatch,
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationSettingsOut:
    return service.patch_my_settings(session, user.organization_id, payload)


@router.get("/me/modules", response_model=OrganizationModulesOut)
def get_my_organization_modules(
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationModulesOut:
    return service.get_my_modules(session, user.organization_id)


@router.patch("/me/modules", response_model=OrganizationModulesOut)
def patch_my_organization_modules(
    payload: OrganizationModulesPatch,
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationModulesOut:
    return service.patch_my_modules(session, user.organization_id, payload)


@router.get("/me/roles", response_model=OrganizationRolesOut)
def get_my_organization_roles(
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationRolesOut:
    return service.list_my_roles(session, user.organization_id)


@router.get("/me/users", response_model=OrganizationUsersOut)
def get_my_organization_users(
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationUsersOut:
    return service.list_my_users(session, user.organization_id)


@router.post("/me/users", response_model=OrganizationUserOut)
def create_my_organization_user(
    payload: OrganizationUserCreate,
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationUserOut:
    return service.create_my_user(session, user.organization_id, payload)


@router.patch("/me/users/{user_id}", response_model=OrganizationUserOut)
def patch_my_organization_user(
    user_id: UUID,
    payload: OrganizationUserPatch,
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationUserOut:
    return service.patch_my_user(session, user.organization_id, user_id, payload, user.id)


@router.put("/me/users/{user_id}/roles", response_model=OrganizationUserOut)
def put_my_organization_user_roles(
    user_id: UUID,
    payload: OrganizationUserRolesPut,
    user: AuthenticatedUser = Depends(current_user),
    _: AuthenticatedUser = Depends(admin_manage),
    session: Session = Depends(get_db_session),
) -> OrganizationUserOut:
    return service.put_my_user_roles(session, user.organization_id, user_id, payload, user.id)
