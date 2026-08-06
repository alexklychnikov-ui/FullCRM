from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, require_permission
from app.auth.service import AuthenticatedUser
from app.db.session import get_db_session
from app.organizations import service
from app.organizations.schemas import (
    OrganizationModulesOut,
    OrganizationModulesPatch,
    OrganizationSettingsOut,
    OrganizationSettingsPatch,
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
