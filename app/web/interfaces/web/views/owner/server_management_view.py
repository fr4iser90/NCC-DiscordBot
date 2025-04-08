from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from app.web.core.extensions import templates_extension, session_extension
from app.web.application.services.auth.dependencies import get_current_user
from app.web.domain.auth.permissions import Role, require_role
from app.web.interfaces.api.rest.v1.owner import (
    get_servers,
    add_server,
    get_server_details,
    update_server_access
)
from app.shared.interface.logging.api import get_web_logger

router = APIRouter(prefix="/owner/servers", tags=["Server Management"])
templates = templates_extension()
logger = get_web_logger()

class ServerManagementView:
    """View for server management functionality"""
    
    def __init__(self):
        self.router = router
        self._register_routes()
    
    def _register_routes(self):
        """Register all routes for this view"""
        self.router.get("", response_class=HTMLResponse)(self.server_management_page)
        self.router.get("/{guild_id}", response_class=HTMLResponse)(self.server_details_page)
    
    async def server_management_page(self, request: Request, current_user=Depends(get_current_user)):
        """Render server management page"""
        try:
            await require_role(current_user, Role.OWNER)
            
            # Get server list
            logger.info("Fetching servers from API...")
            servers = await get_servers(current_user)
            logger.info(f"Received {len(servers)} servers from API")
            
            # Split servers by status
            pending_servers = [s for s in servers if s["access_status"].lower() == "pending"]
            approved_servers = [s for s in servers if s["access_status"].lower() == "approved"]
            blocked_servers = [s for s in servers if s["access_status"].lower() in ["blocked", "rejected"]]
            
            logger.info(f"Filtered servers - Pending: {len(pending_servers)}, Approved: {len(approved_servers)}, Blocked: {len(blocked_servers)}")
            
            for server in pending_servers:
                logger.info(f"Pending server: {server['name']} (ID: {server['guild_id']}) - Status: {server['access_status']}")
            
            return templates.TemplateResponse(
                "views/owner/bot/server-list.html",
                {
                    "request": request,
                    "user": current_user,
                    "active_page": "server-management",
                    "pending_servers": pending_servers,
                    "approved_servers": approved_servers,
                    "blocked_servers": blocked_servers
                }
            )
        except HTTPException as e:
            logger.error(f"Access denied to server management: {e}")
            return templates.TemplateResponse(
                "views/errors/403.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": str(e.detail)
                },
                status_code=403
            )
        except Exception as e:
            logger.error(f"Error in server management view: {e}")
            return templates.TemplateResponse(
                "views/errors/500.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": str(e)
                },
                status_code=500
            )
    
    async def server_details_page(self, guild_id: str, request: Request, current_user=Depends(get_current_user)):
        """Render server details page"""
        try:
            await require_role(current_user, Role.OWNER)
            
            # Get server details
            server = await get_server_details(guild_id, current_user)
            
            return templates.TemplateResponse(
                "views/owner/bot/server-details.html",
                {
                    "request": request,
                    "user": current_user,
                    "active_page": "server-management",
                    "server": server
                }
            )
        except HTTPException as e:
            logger.error(f"Access denied to server details: {e}")
            return templates.TemplateResponse(
                "views/errors/403.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": str(e.detail)
                },
                status_code=403
            )
        except Exception as e:
            logger.error(f"Error in server details view: {e}")
            return templates.TemplateResponse(
                "views/errors/500.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": str(e)
                },
                status_code=500
            )

# Create view instance
server_management_view = ServerManagementView()
