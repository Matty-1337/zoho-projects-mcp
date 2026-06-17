"""
Zoho Projects MCP Server - FastMCP 3.x
OAuth callback stores access token directly.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from fastmcp import FastMCP
from auth import zoho_request, handle_error, PORTAL_ID
from typing import Optional

mcp = FastMCP("zoho_projects_mcp")

def portal_path(path: str) -> str:
    return f"/portal/{PORTAL_ID}{path}"

@mcp.tool
async def zoho_projects_create_tags(tags: list[dict]) -> str:
    """Create portal-level tags. Each tag needs 'name' and optional 'color_class'."""
    try:
        result = await zoho_request("POST", portal_path("/tags"), data={"tags": json.dumps(tags)})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_list_tags(page: int = 1, per_page: int = 50) -> str:
    """List all portal tags with their real IDs needed for task assignment."""
    try:
        result = await zoho_request("GET", portal_path("/tags"), params={"page": page, "per_page": per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_assign_tags_to_task(project_id: str, task_id: str, tag_ids: list[str]) -> str:
    """Assign portal tags to a task."""
    try:
        result = await zoho_request("PATCH", portal_path(f"/projects/{project_id}/tasks/{task_id}"), json={"tags": [{"add": [{"id": tid} for tid in tag_ids]}]})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_bulk_assign_tags(project_id: str, assignments: list[dict]) -> str:
    """Assign tags to multiple tasks at once. assignments: [{'task_id': '123', 'tag_ids': ['456', '789']}]"""
    results = []
    for a in assignments:
        task_id = a.get("task_id")
        tag_ids = a.get("tag_ids", [])
        try:
            await zoho_request("PATCH", portal_path(f"/projects/{project_id}/tasks/{task_id}"), json={"tags": [{"add": [{"id": tid} for tid in tag_ids]}]})
            results.append({"task_id": task_id, "status": "success"})
        except Exception as e:
            results.append({"task_id": task_id, "status": "error", "error": handle_error(e)})
    return json.dumps({"total": len(results), "results": results}, indent=2)

@mcp.tool
async def zoho_projects_list_projects(status: Optional[str] = None, page: int = 1, per_page: int = 50) -> str:
    """List all projects."""
    try:
        p = {"page": page, "per_page": per_page}
        if status: p["status"] = status
        result = await zoho_request("GET", portal_path("/projects"), params=p)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_list_tasks(project_id: str, tasklist_id: Optional[str] = None, page: int = 1, per_page: int = 50) -> str:
    """List tasks in a project."""
    try:
        endpoint = portal_path(f"/projects/{project_id}/tasklists/{tasklist_id}/tasks") if tasklist_id else portal_path(f"/projects/{project_id}/tasks")
        result = await zoho_request("GET", endpoint, params={"page": page, "per_page": per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_create_task(project_id: str, name: str, tasklist_id: Optional[str] = None, description: Optional[str] = None, owner_zpuid: Optional[str] = None, priority: Optional[str] = None, end_date: Optional[str] = None, tag_ids: Optional[list[str]] = None) -> str:
    """Create a task."""
    try:
        body: dict = {"name": name}
        if tasklist_id: body["tasklist"] = {"id": tasklist_id}
        if description: body["description"] = description
        if owner_zpuid: body["owners_and_work"] = {"owners": [{"zpuid": owner_zpuid}]}
        if priority: body["priority"] = priority
        if end_date: body["end_date"] = end_date
        if tag_ids: body["tags"] = [{"add": [{"id": tid} for tid in tag_ids]}]
        result = await zoho_request("POST", portal_path(f"/projects/{project_id}/tasks"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_update_task(project_id: str, task_id: str, name: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, owner_zpuid: Optional[str] = None, end_date: Optional[str] = None, is_completed: Optional[bool] = None, add_tag_ids: Optional[list[str]] = None, remove_tag_ids: Optional[list[str]] = None) -> str:
    """Update a task."""
    try:
        body: dict = {}
        if name: body["name"] = name
        if description: body["description"] = description
        if priority: body["priority"] = priority
        if owner_zpuid: body["owners_and_work"] = {"owners": [{"add": [{"zpuid": owner_zpuid}]}]}
        if end_date: body["end_date"] = end_date
        if is_completed is not None: body["is_completed"] = is_completed
        if add_tag_ids or remove_tag_ids:
            tag_op: dict = {}
            if add_tag_ids: tag_op["add"] = [{"id": tid} for tid in add_tag_ids]
            if remove_tag_ids: tag_op["remove"] = [{"id": tid} for tid in remove_tag_ids]
            body["tags"] = [tag_op]
        result = await zoho_request("PATCH", portal_path(f"/projects/{project_id}/tasks/{task_id}"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_list_portal_users() -> str:
    """List all portal users with ZPUIDs."""
    try:
        result = await zoho_request("GET", portal_path("/users"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_list_tasklists(project_id: str) -> str:
    """List task lists in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/tasklists"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool
async def zoho_projects_search(query: str, project_id: Optional[str] = None) -> str:
    """Search tasks, issues, milestones."""
    try:
        endpoint = portal_path(f"/projects/{project_id}/search") if project_id else portal_path("/search")
        result = await zoho_request("GET", endpoint, params={"search_term": query})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import HTMLResponse
    from starlette.routing import Route, Mount
    from auth import _set_access_token

    CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
    CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
    ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
    REDIRECT_URI = "https://zoho-projects-mcp-production.up.railway.app/oauth/callback"

    async def oauth_callback(request):
        code = request.query_params.get("code")
        if not code:
            return HTMLResponse("<h2>No code received</h2>", status_code=400)
        try:
            data = urllib.parse.urlencode({
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }).encode()
            req = urllib.request.Request(f"{ACCOUNTS_URL}/oauth/v2/token", data=data, method="POST")
            r = urllib.request.urlopen(req, timeout=10)
            result = json.loads(r.read())

            access_token = result.get("access_token")
            refresh_token = result.get("refresh_token")
            expires_in = result.get("expires_in", 3600)

            if access_token:
                # Store access token in memory for immediate use
                _set_access_token(access_token, time.time() + expires_in)

            if refresh_token:
                msg = f"<h2>✅ Full Success!</h2><p>Store this in Railway as ZOHO_REFRESH_TOKEN:</p><pre>{refresh_token}</pre>"
            elif access_token:
                msg = f"<h2>✅ Access Token Captured!</h2><p>Server is authorized for 1 hour.</p><p>To make permanent: store this access token in Railway as ZOHO_ACCESS_TOKEN:</p><pre>{access_token}</pre><p><small>Full response: {json.dumps(result)}</small></p>"
            else:
                msg = f"<h2>❌ Error</h2><pre>{json.dumps(result, indent=2)}</pre>"

            return HTMLResponse(msg)
        except Exception as e:
            return HTMLResponse(f"<h2>❌ Exception</h2><pre>{str(e)}</pre>")

    async def auth_start(request):
        scope = "ZohoProjects.portals.ALL,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.bugs.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoProjects.users.ALL,ZohoProjects.documents.ALL"
        redirect_uri = urllib.parse.quote(REDIRECT_URI)
        url = f"{ACCOUNTS_URL}/oauth/v2/auth?scope={scope}&client_id={CLIENT_ID}&response_type=code&access_type=offline&prompt=consent&redirect_uri={redirect_uri}"
        return HTMLResponse(f'<h2>Authorize Zoho Projects</h2><a href="{url}"><button style="font-size:20px;padding:10px 20px;background:#0066cc;color:white;border:none;border-radius:6px;cursor:pointer">Authorize Now</button></a>')

    port = int(os.environ.get("PORT", 8000))
    mcp_app = mcp.http_app()

    app = Starlette(routes=[
        Route("/oauth/callback", oauth_callback),
        Route("/auth", auth_start),
        Mount("/", app=mcp_app),
    ])

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
