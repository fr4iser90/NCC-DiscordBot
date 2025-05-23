from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.web.interfaces.api.rest.dependencies.auth_dependencies import get_web_db_session # Reuse session dependency

# Import repositories (interfaces and implementations)
from app.shared.domain.repositories.ui.ui_layout_repository import UILayoutRepository
from app.shared.infrastructure.repositories.ui.ui_layout_repository_impl import UILayoutRepositoryImpl

# Import the service
from app.web.application.services.ui.layout_service import LayoutService

# Optional: Dependency provider for individual repositories if needed elsewhere
# def get_layout_repository(session: AsyncSession = Depends(get_web_db_session)) -> UILayoutRepository:
#     """Provides an instance of UILayoutRepositoryImpl with a session."""
#     return UILayoutRepositoryImpl(session)

# def get_shared_layout_template_repository(session: AsyncSession = Depends(get_web_db_session)) -> SharedUILayoutTemplateRepository:
#     """Provides an instance of SharedUILayoutTemplateRepositoryImpl with a session."""
#     return SharedUILayoutTemplateRepositoryImpl(session)

# Updated Dependency provider for LayoutService
async def get_layout_service(
    session: Annotated[AsyncSession, Depends(get_web_db_session)]
) -> LayoutService:
    """Dependency provider for LayoutService, injecting the required repository."""
    user_layout_repo = UILayoutRepositoryImpl(session=session)
    # Pass only the user layout repository to the service constructor
    service = LayoutService(
        layout_repository=user_layout_repo
    )
    return service 