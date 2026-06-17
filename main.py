"""
Zoho Projects MCP Server - FastMCP 3.x
Uses transport="http" which serves at /mcp endpoint
"""

import os
from fastmcp import FastMCP
from auth import zoho_request, handle_error, PORTAL_ID
import json
from typing import Optional

mcp = FastMCP("zoho_projects_mcp")


def portal_path(path: str) -> str:
    return f"/portal/{PORTAL_ID}{path}"


# ── TAGS ──────────────────────────────────────────────────

@mcp.tool
async def zoho_projects_create_tags(tags: list[dict]) -> str:
    """Create portal-level tags. Each tag needs 'name' and optional 'color_class'.
    Example: [{'name': 'Marketing', 'color_class': 'bg0dd3d3'}]"""
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
    """Assign portal tags to a task. tag_ids must be real portal tag IDs from zoho_projects_list_tags."""
    try:
        result = await zoho_request(
            "PATCH",
            portal_path(f"/projects/{project_id}/tasks/{task_id}"),
            json={"tags": [{"add": [{"id": tid} for tid in tag_ids]}]}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_bulk_assign_tags(project_id: str, assignments: list[dict]) -> str:
    """Assign tags to multiple tasks at once.
    assignments: [{'task_id': '123', 'tag_ids': ['456', '789']}, ...]"""
    results = []
    for a in assignments:
        task_id = a.get("task_id")
        tag_ids = a.get("tag_ids", [])
        try:
            await zoho_request(
                "PATCH",
                portal_path(f"/projects/{project_id}/tasks/{task_id}"),
                json={"tags": [{"add": [{"id": tid} for tid in tag_ids]}]}
            )
            results.append({"task_id": task_id, "status": "success"})
        except Exception as e:
            results.append({"task_id": task_id, "status": "error", "error": handle_error(e)})
    return json.dumps({"total": len(results), "results": results}, indent=2)


# ── PORTAL & PROJECTS ─────────────────────────────────────

@mcp.tool
async def zoho_projects_get_portal() -> str:
    """Get portal details including plan, owner, timezone."""
    try:
        result = await zoho_request("GET", portal_path(""))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_list_projects(status: Optional[str] = None, page: int = 1, per_page: int = 50) -> str:
    """List all projects. status: 'active', 'archived', or None for all."""
    try:
        p = {"page": page, "per_page": per_page}
        if status:
            p["status"] = status
        result = await zoho_request("GET", portal_path("/projects"), params=p)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_get_project(project_id: str) -> str:
    """Get full details of a specific project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_create_project(name: str, description: Optional[str] = None,
                                        owner_zpuid: Optional[str] = None,
                                        start_date: Optional[str] = None,
                                        end_date: Optional[str] = None) -> str:
    """Create a new project in the portal."""
    try:
        body: dict = {"name": name, "is_public_project": False}
        if description: body["description"] = description
        if owner_zpuid: body["owner"] = {"zpuid": owner_zpuid}
        if start_date: body["start_date"] = start_date
        if end_date: body["end_date"] = end_date
        result = await zoho_request("POST", portal_path("/projects"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_update_project(project_id: str, name: Optional[str] = None,
                                        description: Optional[str] = None,
                                        status: Optional[str] = None) -> str:
    """Update a project. status: 'active' or 'archived'."""
    try:
        body: dict = {}
        if name: body["name"] = name
        if description: body["description"] = description
        if status: body["project_type"] = status
        result = await zoho_request("PATCH", portal_path(f"/projects/{project_id}"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── TASK LISTS ────────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_tasklists(project_id: str) -> str:
    """List all task lists in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/tasklists"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_create_tasklist(project_id: str, name: str) -> str:
    """Create a new task list in a project."""
    try:
        result = await zoho_request("POST", portal_path(f"/projects/{project_id}/tasklists"), json={"name": name})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── TASKS ─────────────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_tasks(project_id: str, tasklist_id: Optional[str] = None,
                                    page: int = 1, per_page: int = 50) -> str:
    """List tasks in a project, optionally filtered by task list."""
    try:
        endpoint = portal_path(f"/projects/{project_id}/tasklists/{tasklist_id}/tasks") if tasklist_id else portal_path(f"/projects/{project_id}/tasks")
        result = await zoho_request("GET", endpoint, params={"page": page, "per_page": per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_get_task(project_id: str, task_id: str) -> str:
    """Get full details of a task including tags, owner, status."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/tasks/{task_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_create_task(project_id: str, name: str,
                                     tasklist_id: Optional[str] = None,
                                     description: Optional[str] = None,
                                     owner_zpuid: Optional[str] = None,
                                     priority: Optional[str] = None,
                                     end_date: Optional[str] = None,
                                     tag_ids: Optional[list[str]] = None) -> str:
    """Create a task. priority: 'high', 'medium', 'low'. end_date: YYYY-MM-DD."""
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
async def zoho_projects_update_task(project_id: str, task_id: str,
                                     name: Optional[str] = None,
                                     description: Optional[str] = None,
                                     priority: Optional[str] = None,
                                     owner_zpuid: Optional[str] = None,
                                     end_date: Optional[str] = None,
                                     is_completed: Optional[bool] = None,
                                     add_tag_ids: Optional[list[str]] = None,
                                     remove_tag_ids: Optional[list[str]] = None) -> str:
    """Update any task field. add_tag_ids/remove_tag_ids: portal tag IDs."""
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
async def zoho_projects_delete_task(project_id: str, task_id: str) -> str:
    """Permanently delete a task."""
    try:
        result = await zoho_request("DELETE", portal_path(f"/projects/{project_id}/tasks/{task_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── USERS ─────────────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_portal_users() -> str:
    """List all portal users with their ZPUIDs."""
    try:
        result = await zoho_request("GET", portal_path("/users"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_list_project_users(project_id: str) -> str:
    """List users in a specific project with their ZPUIDs and roles."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/users"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_add_users_to_project(project_id: str, users: list[dict]) -> str:
    """Add users to a project. users: [{'email_id': 'x@y.com', 'role_id': '123', 'profile_id': '456'}]"""
    try:
        result = await zoho_request(
            "POST",
            portal_path(f"/projects/{project_id}/users"),
            data={"notify": False, "userdetails": json.dumps(users)}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── ISSUES / BUGS ─────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_issues(project_id: str, page: int = 1, per_page: int = 50) -> str:
    """List all bugs/issues in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/issues"), params={"page": page, "per_page": per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_create_issue(project_id: str, name: str,
                                      description: Optional[str] = None,
                                      assignee_zpuid: Optional[str] = None) -> str:
    """Create a bug/issue in a project."""
    try:
        body: dict = {"name": name}
        if description: body["description"] = description
        if assignee_zpuid: body["assignee"] = {"zpuid": assignee_zpuid}
        result = await zoho_request("POST", portal_path(f"/projects/{project_id}/issues"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── MILESTONES ────────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_phases(project_id: str) -> str:
    """List all phases/milestones in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/phases"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── TIMELOGS ──────────────────────────────────────────────

@mcp.tool
async def zoho_projects_list_timelogs(project_id: str, page: int = 1, per_page: int = 50) -> str:
    """List time logs in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{project_id}/logs"), params={"page": page, "per_page": per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── SEARCH ────────────────────────────────────────────────

@mcp.tool
async def zoho_projects_search(query: str, project_id: Optional[str] = None) -> str:
    """Search across tasks, issues, milestones in the portal or a specific project."""
    try:
        endpoint = portal_path(f"/projects/{project_id}/search") if project_id else portal_path("/search")
        result = await zoho_request("GET", endpoint, params={"search_term": query})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── COMMENTS ──────────────────────────────────────────────

@mcp.tool
async def zoho_projects_add_task_comment(project_id: str, task_id: str, content: str) -> str:
    """Add a comment to a task."""
    try:
        result = await zoho_request("POST", portal_path(f"/projects/{project_id}/tasks/{task_id}/comments"), json={"content": content})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ── SETTINGS ──────────────────────────────────────────────

@mcp.tool
async def zoho_projects_get_fields(module: str) -> str:
    """Get field definitions for a module. module: 'tasks', 'issues', 'projects'."""
    try:
        result = await zoho_request("GET", portal_path("/settings/fields"), params={"module": module})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_list_profiles() -> str:
    """List user profiles in the portal (needed for adding users to projects)."""
    try:
        result = await zoho_request("GET", portal_path("/settings/profiles"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool
async def zoho_projects_list_roles() -> str:
    """List user roles in the portal."""
    try:
        result = await zoho_request("GET", portal_path("/settings/roles"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
