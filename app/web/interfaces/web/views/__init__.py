from .admin.index_view import router as admin_router
from .admin.user_management_view import router as user_management_router
from .auth.auth_view import router as auth_router
from .home.overview import router as home_router
from .main.main_view import router as main_router
from .navbar.server_selector_view import router as server_selector_router
from .debug.debug_view import router as debug_router
from .guild.user_management_view import router as guild_user_management_router
from .owner.owner_view import router as owner_router
from .owner.bot_control_view import router as bot_control_router
# Liste aller Web-View-Router
routers = [
    main_router,
    admin_router,
    user_management_router,
    auth_router,
    home_router,
    server_selector_router,
    debug_router,   
    guild_user_management_router,
    owner_router,
    bot_control_router
] 