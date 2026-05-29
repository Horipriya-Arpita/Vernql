"""
User Model
Represents a user account that belongs to a company
"""
import enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class UserRole(str, enum.Enum):
    """
    Company-scoped roles — controls what a user can do within their company.

    VIEWER  — read-only: can run queries and view results, cannot modify schemas
    EDITOR  — default: full read/write access to schemas and queries
    ADMIN   — company administrator: all EDITOR permissions + manage users/API keys
    """
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN  = "admin"


# Role precedence for permission checks (higher index = more permissions)
_ROLE_ORDER = [UserRole.VIEWER, UserRole.EDITOR, UserRole.ADMIN]


def user_has_role(user: "User", minimum_role: UserRole) -> bool:
    """Return True if the user's role is at least `minimum_role`."""
    try:
        return _ROLE_ORDER.index(UserRole(user.role)) >= _ROLE_ORDER.index(minimum_role)
    except (ValueError, TypeError):
        return False


class User(Base):
    """
    User entity - represents individual users within a company
    Each user authenticates with email/password and belongs to a company
    """
    __tablename__ = "users"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Company Relationship
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # Legacy — prefer `role`

    # RBAC role (defaults to EDITOR so existing users retain full access)
    role = Column(
        String(20),
        nullable=False,
        default=UserRole.EDITOR,
        server_default="editor",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    company = relationship("Company", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, company_id={self.company_id})>"