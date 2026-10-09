from fastapi import APIRouter, HTTPException

from app import db, jira_client
from app.runtime.docker_manager import DockerManager
from app.models import (
    JiraIssue,
    JiraAssigneeUpdate,
    Project,
    ProjectCreate,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects() -> list[Project]:
    return db.list_projects()


@router.post("", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    return db.create_project(payload)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: int) -> Project:
    project = db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: int, payload: ProjectUpdate) -> Project:
    project = db.update_project(project_id, payload)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int) -> None:
    if not db.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}/issues", response_model=list[JiraIssue])
def get_project_issues(project_id: int) -> list[JiraIssue]:
    project = db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return jira_client.fetch_project_issues(project.jira_project_url)
    except jira_client.JiraConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except jira_client.JiraApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@router.get("/{project_id}/issues/{issue_key}/assignees")
def get_issue_assignees(
    project_id: int,
    issue_key: str,
) -> list[dict]:
    project = db.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        server_url = jira_client.parse_server_url(
            project.jira_project_url
        )

        return jira_client.fetch_assignable_users(
            issue_key,
            server_url,
        )

    except jira_client.JiraConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except jira_client.JiraApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@router.put("/{project_id}/issues/{issue_key}/assignee")
def update_issue_assignee(
    project_id: int,
    issue_key: str,
    payload: JiraAssigneeUpdate,
        ) -> dict:
    project = db.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        server_url = jira_client.parse_server_url(
            project.jira_project_url
        )

        jira_client.assign_issue(
            issue_key,
            payload.account_id,
            server_url,
        )

        return {
            "message": "Issue assigned successfully",
            "issue_key": issue_key,
            "account_id": payload.account_id,
        }

    except jira_client.JiraConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except jira_client.JiraApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
    project = db.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        server_url = jira_client.parse_server_url(
            project.jira_project_url
        )

        jira_client.assign_issue(
            issue_key,
            account_id,
            server_url,
        )

        return {
            "message": "Issue assigned successfully",
            "issue_key": issue_key,
            "account_id": account_id,
        }

    except jira_client.JiraConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except jira_client.JiraApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

@router.post("/{project_id}/issues/{issue_key}/start")
def start_issue(
    project_id: int,
    issue_key: str,
) -> dict:
    project = db.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        server_url = jira_client.parse_server_url(
            project.jira_project_url
        )

        issues = jira_client.fetch_project_issues(
            project.jira_project_url
        )

        issue = next(
    (
        item
        for item in issues
        if item["key"].upper() == issue_key.upper()
            ),
        None,
           )


        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Jira issue {issue_key} not found",
            )

        docker_manager = DockerManager()

        container = docker_manager.spawn_worker(
            task_id=issue["key"],
            task_title=issue["title"],
            task_description=(
            f"Implement Jira issue {issue['key']}: "
            f"{issue['title']}"
),
        )

        jira_client.transition_issue(
            issue["key"],
            "IN PROGRESS",
            server_url,
        )

        return {
            "message": "Issue started successfully",
            "issue_key": issue["key"],
            "status": "IN PROGRESS",
            "container_id": container.id,
        }

    except jira_client.JiraConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except jira_client.JiraApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start issue: {exc}",
        ) from exc

@router.post("/webhooks/github")
def github_webhook(payload: dict) -> dict:
    action = payload.get("action")

    pull_request = payload.get("pull_request", {})

    if action != "closed":
        return {
            "message": "Webhook ignored",
            "reason": "Pull request is not closed",
        }

    if not pull_request.get("merged"):
        return {
            "message": "Webhook ignored",
            "reason": "Pull request was closed without merging",
        }

    branch_name = (
        pull_request
        .get("head", {})
        .get("ref", "")
    )

    if not branch_name.startswith("feat/"):
        return {
            "message": "Webhook ignored",
            "reason": "Branch does not follow feat/<JIRA-KEY> format",
        }

    issue_key = branch_name.removeprefix("feat/")

    try:
        server_url = jira_client.parse_server_url(
            db.get_project(1).jira_project_url
        )

        jira_client.transition_issue(
            issue_key,
            "Done",
            server_url,
        )

        return {
            "message": "Pull request merged and Jira issue marked Done",
            "issue_key": issue_key,
            "status": "Done",
        }

    except jira_client.JiraConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except jira_client.JiraApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
