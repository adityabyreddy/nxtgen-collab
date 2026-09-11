from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import db
from app.models import Contributor, ContributorRole, ProjectCreate, ProjectUpdate

router = APIRouter(tags=["web"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ROLES = [r.value for r in ContributorRole]


async def _parse_contributors(request: Request) -> list[Contributor]:
    form = await request.form()
    names = form.getlist("contributor_name")
    roles = form.getlist("contributor_role")
    contributors = []
    for name, role in zip(names, roles):
        if name.strip():
            contributors.append(Contributor(name=name.strip(), role=ContributorRole(role)))
    return contributors


@router.get("/")
def index(request: Request):
    projects = db.list_projects()
    return templates.TemplateResponse(
        request, "projects_list.html", {"projects": projects}
    )


@router.get("/projects/new")
def new_project_form(request: Request):
    return templates.TemplateResponse(
        request,
        "project_form.html",
        {"project": None, "roles": ROLES, "mode": "create"},
    )


@router.post("/projects/new")
async def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    git_repo_url: str = Form(""),
    jira_project_url: str = Form(""),
):
    contributors = await _parse_contributors(request)
    payload = ProjectCreate(
        name=name,
        description=description,
        git_repo_url=git_repo_url,
        jira_project_url=jira_project_url,
        contributors=contributors,
    )
    project = db.create_project(payload)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@router.get("/projects/{project_id}")
def view_project(request: Request, project_id: int):
    project = db.get_project(project_id)
    if project is None:
        return templates.TemplateResponse(
            request, "not_found.html", {}, status_code=404
        )
    return templates.TemplateResponse(
        request, "project_detail.html", {"project": project}
    )


@router.get("/projects/{project_id}/issues")
def view_project_issues(request: Request, project_id: int):
    project = db.get_project(project_id)
    if project is None:
        return templates.TemplateResponse(
            request, "not_found.html", {}, status_code=404
        )
    return templates.TemplateResponse(
        request, "project_issues.html", {"project": project}
    )


@router.get("/projects/{project_id}/edit")
def edit_project_form(request: Request, project_id: int):
    project = db.get_project(project_id)
    if project is None:
        return templates.TemplateResponse(
            request, "not_found.html", {}, status_code=404
        )
    return templates.TemplateResponse(
        request,
        "project_form.html",
        {"project": project, "roles": ROLES, "mode": "edit"},
    )


@router.post("/projects/{project_id}/edit")
async def update_project(
    request: Request,
    project_id: int,
    name: str = Form(...),
    description: str = Form(""),
    git_repo_url: str = Form(""),
    jira_project_url: str = Form(""),
):
    contributors = await _parse_contributors(request)
    payload = ProjectUpdate(
        name=name,
        description=description,
        git_repo_url=git_repo_url,
        jira_project_url=jira_project_url,
        contributors=contributors,
    )
    project = db.update_project(project_id, payload)
    if project is None:
        return templates.TemplateResponse(
            request, "not_found.html", {}, status_code=404
        )
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@router.post("/projects/{project_id}/delete")
def delete_project(project_id: int):
    db.delete_project(project_id)
    return RedirectResponse(url="/", status_code=303)
