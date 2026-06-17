"""
Zoho Projects MCP Tools — Full API v3 Coverage
Covers: Tags, Tasks, Task Lists, Projects, Portals, Users, Timesheets,
        Bugs/Issues, Milestones/Phases, Forums, Events, Pages, Search,
        Activities, Attachments, Comments, Custom Fields, Layouts, Profiles, Roles
"""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from auth import zoho_request, handle_error, PORTAL_ID

mcp = FastMCP("zoho_projects_mcp")


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def portal_path(path: str) -> str:
    return f"/portal/{PORTAL_ID}{path}"


# ═══════════════════════════════════════════════════════════
# TAGS  ← The whole reason we built this server
# ═══════════════════════════════════════════════════════════

class CreateTagsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    tags: list[dict] = Field(..., description="List of tag objects. Each must have 'name' (str) and optionally 'color_class' (str, e.g. 'bg0dd3d3'). Example: [{'name': 'Marketing', 'color_class': 'bg0dd3d3'}]")

@mcp.tool(name="zoho_projects_create_tags", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_tags(params: CreateTagsInput) -> str:
    """Create one or more portal-level tags in Zoho Projects.

    This creates real portal tags (not picklist options) that can be assigned
    to tasks, issues, task lists, projects, forums, and status items.

    Args:
        params.tags: List of tag dicts with 'name' and optional 'color_class'

    Returns:
        JSON with created tag IDs and names
    """
    try:
        result = await zoho_request("POST", portal_path("/tags"), data={"tags": json.dumps(params.tags)})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class ListTagsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    per_page: Optional[int] = Field(default=50, description="Results per page", ge=1, le=200)

@mcp.tool(name="zoho_projects_list_tags", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_tags(params: ListTagsInput) -> str:
    """List all portal-level tags in Zoho Projects with their IDs.

    Returns the real tag entity IDs needed to assign tags to tasks.

    Returns:
        JSON list of tags with id, name, color_class
    """
    try:
        result = await zoho_request("GET", portal_path("/tags"), params={"page": params.page, "per_page": params.per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class AssignTagsToTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")
    tag_ids: list[str] = Field(..., description="List of portal tag IDs to assign to the task")

@mcp.tool(name="zoho_projects_assign_tags_to_task", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_assign_tags_to_task(params: AssignTagsToTaskInput) -> str:
    """Assign one or more portal tags to a specific task.

    Args:
        params.project_id: The project ID containing the task
        params.task_id: The task ID to tag
        params.tag_ids: List of portal-level tag IDs (from zoho_projects_list_tags)

    Returns:
        JSON confirmation of tag assignment
    """
    try:
        tags_payload = [{"add": [{"id": tid} for tid in params.tag_ids]}]
        result = await zoho_request(
            "PATCH",
            portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}"),
            json={"tags": tags_payload}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class DeleteTagInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    tag_id: str = Field(..., description="Tag ID to delete")

@mcp.tool(name="zoho_projects_delete_tag", annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_delete_tag(params: DeleteTagInput) -> str:
    """Delete a portal-level tag from Zoho Projects."""
    try:
        result = await zoho_request("DELETE", portal_path(f"/tags/{params.tag_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# PORTAL
# ═══════════════════════════════════════════════════════════

@mcp.tool(name="zoho_projects_get_portal", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_get_portal() -> str:
    """Get details of the Zoho Projects portal including plan, owner, timezone, settings."""
    try:
        result = await zoho_request("GET", portal_path(""))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="zoho_projects_list_portal_users", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_portal_users() -> str:
    """List all users in the Zoho Projects portal with their ZPUIDs."""
    try:
        result = await zoho_request("GET", portal_path("/users"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# PROJECTS
# ═══════════════════════════════════════════════════════════

class ListProjectsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: Optional[str] = Field(default=None, description="Filter by status: 'active', 'archived', 'template'")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=50, ge=1, le=200)

@mcp.tool(name="zoho_projects_list_projects", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_projects(params: ListProjectsInput) -> str:
    """List all projects in the portal. Supports filtering by status."""
    try:
        p = {"page": params.page, "per_page": params.per_page}
        if params.status:
            p["status"] = params.status
        result = await zoho_request("GET", portal_path("/projects"), params=p)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class GetProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")

@mcp.tool(name="zoho_projects_get_project", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_get_project(params: GetProjectInput) -> str:
    """Get full details of a specific project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class CreateProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(..., description="Project name", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="Project description")
    owner_zpuid: Optional[str] = Field(default=None, description="ZPUID of the project owner")
    start_date: Optional[str] = Field(default=None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date YYYY-MM-DD")
    is_public: Optional[bool] = Field(default=False, description="Whether project is public")

@mcp.tool(name="zoho_projects_create_project", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_project(params: CreateProjectInput) -> str:
    """Create a new project in the Zoho Projects portal."""
    try:
        body: dict = {"name": params.name, "is_public_project": params.is_public}
        if params.description:
            body["description"] = params.description
        if params.owner_zpuid:
            body["owner"] = {"zpuid": params.owner_zpuid}
        if params.start_date:
            body["start_date"] = params.start_date
        if params.end_date:
            body["end_date"] = params.end_date
        result = await zoho_request("POST", portal_path("/projects"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class UpdateProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    name: Optional[str] = Field(default=None, description="New project name")
    description: Optional[str] = Field(default=None, description="New description")
    status: Optional[str] = Field(default=None, description="Status: 'active', 'archived'")
    owner_zpuid: Optional[str] = Field(default=None, description="New owner ZPUID")

@mcp.tool(name="zoho_projects_update_project", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_update_project(params: UpdateProjectInput) -> str:
    """Update an existing project's name, description, status, or owner."""
    try:
        body: dict = {}
        if params.name:
            body["name"] = params.name
        if params.description:
            body["description"] = params.description
        if params.status:
            body["project_type"] = params.status
        if params.owner_zpuid:
            body["owner"] = {"zpuid": params.owner_zpuid}
        result = await zoho_request("PATCH", portal_path(f"/projects/{params.project_id}"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class AddUsersToProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    users: list[dict] = Field(..., description="List of user dicts with 'email_id', 'role_id', 'profile_id'. Example: [{'email_id': 'user@example.com', 'role_id': '123', 'profile_id': '456'}]")

@mcp.tool(name="zoho_projects_add_users_to_project", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_add_users_to_project(params: AddUsersToProjectInput) -> str:
    """Add users to a project with specified roles."""
    try:
        result = await zoho_request(
            "POST",
            portal_path(f"/projects/{params.project_id}/users"),
            data={"notify": False, "userdetails": json.dumps(params.users)}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# TASK LISTS
# ═══════════════════════════════════════════════════════════

class TaskListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")

@mcp.tool(name="zoho_projects_list_tasklists", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_tasklists(params: TaskListInput) -> str:
    """List all task lists in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/tasklists"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class CreateTaskListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Task list name", min_length=1, max_length=200)

@mcp.tool(name="zoho_projects_create_tasklist", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_tasklist(params: CreateTaskListInput) -> str:
    """Create a new task list within a project."""
    try:
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/tasklists"), json={"name": params.name})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# TASKS
# ═══════════════════════════════════════════════════════════

class ListTasksInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    tasklist_id: Optional[str] = Field(default=None, description="Optional task list ID to filter by")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=50, ge=1, le=200)

@mcp.tool(name="zoho_projects_list_tasks", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_tasks(params: ListTasksInput) -> str:
    """List tasks in a project, optionally filtered by task list."""
    try:
        p: dict = {"page": params.page, "per_page": params.per_page}
        endpoint = portal_path(f"/projects/{params.project_id}/tasks")
        if params.tasklist_id:
            endpoint = portal_path(f"/projects/{params.project_id}/tasklists/{params.tasklist_id}/tasks")
        result = await zoho_request("GET", endpoint, params=p)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class GetTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")

@mcp.tool(name="zoho_projects_get_task", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_get_task(params: GetTaskInput) -> str:
    """Get full details of a specific task including tags, owner, status, priority."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class CreateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Task name", min_length=1, max_length=200)
    tasklist_id: Optional[str] = Field(default=None, description="Task list ID to place task in")
    description: Optional[str] = Field(default=None, description="Task description")
    owner_zpuid: Optional[str] = Field(default=None, description="Owner ZPUID")
    priority: Optional[str] = Field(default=None, description="Priority: 'high', 'medium', 'low', 'none'")
    start_date: Optional[str] = Field(default=None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="Due date YYYY-MM-DD")
    tag_ids: Optional[list[str]] = Field(default=None, description="List of portal tag IDs to assign")

@mcp.tool(name="zoho_projects_create_task", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_task(params: CreateTaskInput) -> str:
    """Create a new task in a project with full field support including tags."""
    try:
        body: dict = {"name": params.name}
        if params.tasklist_id:
            body["tasklist"] = {"id": params.tasklist_id}
        if params.description:
            body["description"] = params.description
        if params.owner_zpuid:
            body["owners_and_work"] = {"owners": [{"zpuid": params.owner_zpuid}]}
        if params.priority:
            body["priority"] = params.priority
        if params.start_date:
            body["start_date"] = params.start_date
        if params.end_date:
            body["end_date"] = params.end_date
        if params.tag_ids:
            body["tags"] = [{"add": [{"id": tid} for tid in params.tag_ids]}]
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/tasks"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class UpdateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")
    name: Optional[str] = Field(default=None, description="New task name")
    description: Optional[str] = Field(default=None, description="New description")
    priority: Optional[str] = Field(default=None, description="Priority: 'high', 'medium', 'low', 'none'")
    status_id: Optional[str] = Field(default=None, description="Status ID")
    owner_zpuid: Optional[str] = Field(default=None, description="New owner ZPUID")
    end_date: Optional[str] = Field(default=None, description="Due date YYYY-MM-DD")
    is_completed: Optional[bool] = Field(default=None, description="Mark task complete/incomplete")
    add_tag_ids: Optional[list[str]] = Field(default=None, description="Tag IDs to add")
    remove_tag_ids: Optional[list[str]] = Field(default=None, description="Tag IDs to remove")

@mcp.tool(name="zoho_projects_update_task", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_update_task(params: UpdateTaskInput) -> str:
    """Update any field on a task including tags, priority, status, owner, due date."""
    try:
        body: dict = {}
        if params.name:
            body["name"] = params.name
        if params.description:
            body["description"] = params.description
        if params.priority:
            body["priority"] = params.priority
        if params.status_id:
            body["status"] = {"id": params.status_id}
        if params.owner_zpuid:
            body["owners_and_work"] = {"owners": [{"add": [{"zpuid": params.owner_zpuid}]}]}
        if params.end_date:
            body["end_date"] = params.end_date
        if params.is_completed is not None:
            body["is_completed"] = params.is_completed
        if params.add_tag_ids or params.remove_tag_ids:
            tag_op: dict = {}
            if params.add_tag_ids:
                tag_op["add"] = [{"id": tid} for tid in params.add_tag_ids]
            if params.remove_tag_ids:
                tag_op["remove"] = [{"id": tid} for tid in params.remove_tag_ids]
            body["tags"] = [tag_op]
        result = await zoho_request("PATCH", portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class DeleteTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")

@mcp.tool(name="zoho_projects_delete_task", annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_delete_task(params: DeleteTaskInput) -> str:
    """Permanently delete a task from a project."""
    try:
        result = await zoho_request("DELETE", portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# TASK COMMENTS
# ═══════════════════════════════════════════════════════════

class AddTaskCommentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")
    content: str = Field(..., description="Comment content (plain text or HTML)")

@mcp.tool(name="zoho_projects_add_task_comment", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_add_task_comment(params: AddTaskCommentInput) -> str:
    """Add a comment to a task."""
    try:
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}/comments"), json={"content": params.content})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class ListTaskCommentsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: str = Field(..., description="Task ID")

@mcp.tool(name="zoho_projects_list_task_comments", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_task_comments(params: ListTaskCommentsInput) -> str:
    """List all comments on a task."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/tasks/{params.task_id}/comments"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# BUGS / ISSUES
# ═══════════════════════════════════════════════════════════

class ListIssuesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=50, ge=1, le=200)

@mcp.tool(name="zoho_projects_list_issues", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_issues(params: ListIssuesInput) -> str:
    """List all bugs/issues in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/issues"), params={"page": params.page, "per_page": params.per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class CreateIssueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Issue title", min_length=1)
    description: Optional[str] = Field(default=None)
    assignee_zpuid: Optional[str] = Field(default=None, description="Assignee ZPUID")
    due_date: Optional[str] = Field(default=None, description="Due date ISO format")
    tag_ids: Optional[list[str]] = Field(default=None, description="Portal tag IDs")

@mcp.tool(name="zoho_projects_create_issue", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_issue(params: CreateIssueInput) -> str:
    """Create a new bug/issue in a project."""
    try:
        body: dict = {"name": params.name}
        if params.description:
            body["description"] = params.description
        if params.assignee_zpuid:
            body["assignee"] = {"zpuid": params.assignee_zpuid}
        if params.due_date:
            body["due_date"] = params.due_date
        if params.tag_ids:
            body["tags"] = [{"id": tid} for tid in params.tag_ids]
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/issues"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# MILESTONES / PHASES
# ═══════════════════════════════════════════════════════════

class ListPhasesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")

@mcp.tool(name="zoho_projects_list_phases", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_phases(params: ListPhasesInput) -> str:
    """List all phases/milestones in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/phases"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class CreatePhaseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Phase/milestone name")
    start_date: Optional[str] = Field(default=None, description="Start date ISO format")
    end_date: Optional[str] = Field(default=None, description="End date ISO format")
    owner_zpuid: Optional[str] = Field(default=None, description="Owner ZPUID")

@mcp.tool(name="zoho_projects_create_phase", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_create_phase(params: CreatePhaseInput) -> str:
    """Create a new phase/milestone in a project."""
    try:
        body: dict = {"name": params.name}
        if params.start_date:
            body["start_date"] = params.start_date
        if params.end_date:
            body["end_date"] = params.end_date
        if params.owner_zpuid:
            body["owner_zpuid"] = params.owner_zpuid
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/phases"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# TIMESHEETS
# ═══════════════════════════════════════════════════════════

class ListTimelogsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=50, ge=1, le=200)

@mcp.tool(name="zoho_projects_list_timelogs", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_timelogs(params: ListTimelogsInput) -> str:
    """List all time log entries in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/logs"), params={"page": params.page, "per_page": params.per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class LogTimeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    task_id: Optional[str] = Field(default=None, description="Task ID (required if type is 'task')")
    log_type: str = Field(..., description="Log type: 'task', 'issue', or 'general'")
    hours: str = Field(..., description="Hours in HH:MM format e.g. '02:30'")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    bill_status: str = Field(default="Non Billable", description="'Billable' or 'Non Billable'")
    notes: Optional[str] = Field(default=None, description="Time log notes")

@mcp.tool(name="zoho_projects_log_time", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def zoho_projects_log_time(params: LogTimeInput) -> str:
    """Log time against a task, issue, or general project work."""
    try:
        body: dict = {
            "date": params.date,
            "bill_status": params.bill_status,
            "hours": params.hours,
            "module": {"type": params.log_type},
        }
        if params.task_id:
            body["module"]["id"] = params.task_id
        if params.notes:
            body["notes"] = params.notes
        result = await zoho_request("POST", portal_path(f"/projects/{params.project_id}/logs"), json=body)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════

class ListProjectUsersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")

@mcp.tool(name="zoho_projects_list_project_users", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_project_users(params: ListProjectUsersInput) -> str:
    """List all users in a specific project with their ZPUIDs and roles."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/users"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════════

class SearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Search term")
    project_id: Optional[str] = Field(default=None, description="Scope to a specific project")
    module: Optional[str] = Field(default=None, description="Module to search: 'tasks', 'issues', 'milestones', 'forums'")

@mcp.tool(name="zoho_projects_search", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_search(params: SearchInput) -> str:
    """Search across Zoho Projects for tasks, issues, milestones, or forums."""
    try:
        p: dict = {"search_term": params.query}
        if params.module:
            p["module"] = params.module
        endpoint = portal_path(f"/projects/{params.project_id}/search") if params.project_id else portal_path("/search")
        result = await zoho_request("GET", endpoint, params=p)
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# ACTIVITIES
# ═══════════════════════════════════════════════════════════

class ListActivitiesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=50, ge=1, le=200)

@mcp.tool(name="zoho_projects_list_activities", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_activities(params: ListActivitiesInput) -> str:
    """List recent activities/events in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/activities"), params={"page": params.page, "per_page": params.per_page})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# FORUMS
# ═══════════════════════════════════════════════════════════

class ListForumsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")

@mcp.tool(name="zoho_projects_list_forums", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_forums(params: ListForumsInput) -> str:
    """List all forum posts in a project."""
    try:
        result = await zoho_request("GET", portal_path(f"/projects/{params.project_id}/forums"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# CUSTOM FIELDS / SETTINGS
# ═══════════════════════════════════════════════════════════

class GetFieldsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    module: str = Field(..., description="Module name: 'tasks', 'issues', 'projects', 'tasklists'")

@mcp.tool(name="zoho_projects_get_fields", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_get_fields(params: GetFieldsInput) -> str:
    """Get all field definitions for a module including custom fields and their IDs."""
    try:
        result = await zoho_request("GET", portal_path("/settings/fields"), params={"module": params.module})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


class GetLayoutsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    module: str = Field(..., description="Module: 'tasks', 'issues', 'projects'")

@mcp.tool(name="zoho_projects_get_layouts", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_get_layouts(params: GetLayoutsInput) -> str:
    """Get all layouts configured for a module."""
    try:
        result = await zoho_request("GET", portal_path("/settings/layouts"), params={"module": params.module})
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# PROFILES & ROLES
# ═══════════════════════════════════════════════════════════

@mcp.tool(name="zoho_projects_list_profiles", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_profiles() -> str:
    """List all user profiles in the portal with their IDs (needed for adding users to projects)."""
    try:
        result = await zoho_request("GET", portal_path("/settings/profiles"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="zoho_projects_list_roles", annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_list_roles() -> str:
    """List all user roles in the portal with their IDs."""
    try:
        result = await zoho_request("GET", portal_path("/settings/roles"))
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(e)


# ═══════════════════════════════════════════════════════════
# BULK TAG ASSIGNMENT (Power tool)
# ═══════════════════════════════════════════════════════════

class BulkAssignTagsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: str = Field(..., description="Project ID")
    assignments: list[dict] = Field(..., description="List of dicts with 'task_id' and 'tag_ids' (list of tag ID strings). Example: [{'task_id': '123', 'tag_ids': ['456', '789']}]")

@mcp.tool(name="zoho_projects_bulk_assign_tags", annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def zoho_projects_bulk_assign_tags(params: BulkAssignTagsInput) -> str:
    """Assign tags to multiple tasks at once. Processes all assignments sequentially.

    This is the power tool for tagging all tasks in Jess's board at once.

    Args:
        params.project_id: The project containing all tasks
        params.assignments: List of {task_id, tag_ids} pairs

    Returns:
        JSON summary of all assignment results with success/failure per task
    """
    results = []
    for assignment in params.assignments:
        task_id = assignment.get("task_id")
        tag_ids = assignment.get("tag_ids", [])
        try:
            tags_payload = [{"add": [{"id": tid} for tid in tag_ids]}]
            result = await zoho_request(
                "PATCH",
                portal_path(f"/projects/{params.project_id}/tasks/{task_id}"),
                json={"tags": tags_payload}
            )
            results.append({"task_id": task_id, "status": "success", "tag_ids": tag_ids})
        except Exception as e:
            results.append({"task_id": task_id, "status": "error", "error": handle_error(e), "tag_ids": tag_ids})
    return json.dumps({"total": len(results), "results": results}, indent=2)
