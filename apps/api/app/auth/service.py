from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModuleToggle, Organization, Permission, Role, RolePermission, User, UserRole


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    organization_id: UUID
    email: str
    full_name: str
    is_active: bool
    organization_name: str
    organization_slug: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    modules: tuple[str, ...]

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_module(self, module_key: str) -> bool:
        return module_key in self.modules

    def to_profile(self) -> dict[str, object]:
        return {
            "user": {
                "id": str(self.id),
                "email": self.email,
                "fullName": self.full_name,
                "isActive": self.is_active,
            },
            "organization": {
                "id": str(self.organization_id),
                "name": self.organization_name,
                "slug": self.organization_slug,
            },
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "modules": list(self.modules),
        }


def get_user_profile_by_id(session: Session, user_id: UUID) -> AuthenticatedUser | None:
    user = session.get(User, user_id)

    if user is None:
        return None

    return build_user_profile(session, user)


def build_user_profile(session: Session, user: User) -> AuthenticatedUser | None:
    organization = session.get(Organization, user.organization_id)

    if organization is None:
        return None

    roles = tuple(
        sorted(
            session.scalars(
                select(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(
                    UserRole.user_id == user.id,
                    UserRole.organization_id == user.organization_id,
                    Role.organization_id == user.organization_id,
                )
            ).all()
        )
    )
    permissions = tuple(
        sorted(
            session.scalars(
                select(Permission.key)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(UserRole, UserRole.role_id == RolePermission.role_id)
                .where(
                    UserRole.user_id == user.id,
                    UserRole.organization_id == user.organization_id,
                    RolePermission.organization_id == user.organization_id,
                )
            ).all()
        )
    )
    modules = tuple(
        sorted(
            session.scalars(
                select(ModuleToggle.module_key).where(
                    ModuleToggle.organization_id == user.organization_id,
                    ModuleToggle.enabled.is_(True),
                )
            ).all()
        )
    )

    return AuthenticatedUser(
        id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        organization_name=organization.name,
        organization_slug=organization.slug,
        roles=roles,
        permissions=permissions,
        modules=modules,
    )
