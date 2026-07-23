from enum import StrEnum


class UserStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    locked = "locked"


class ModuleStatus(StrEnum):
    active = "active"
    inactive = "inactive"


class MembershipRole(StrEnum):
    admin = "admin"
    user = "user"


class MembershipStatus(StrEnum):
    active = "active"
    inactive = "inactive"


class RefreshTokenStatus(StrEnum):
    active = "active"
    revoked = "revoked"
