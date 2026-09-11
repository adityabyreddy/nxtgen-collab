from fastapi import APIRouter, HTTPException

from app import db, jira_client
from app.models import JiraIssue, Project, ProjectCreate, ProjectUpdate

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
