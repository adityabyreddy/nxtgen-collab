from enum import Enum

from pydantic import BaseModel, Field


class ContributorRole(str, Enum):
    DEV = "Dev"
    QA = "QA"
    DEVOPS = "DevOps"
    AI_DEV = "AI Dev"
    AI_QA = "AI QA"
    AI_DEVOPS = "AI DevOps"


class Contributor(BaseModel):
    name: str
    role: ContributorRole


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    git_repo_url: str = ""
    jira_project_url: str = ""
    contributors: list[Contributor] = []


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: str
    updated_at: str


class JiraIssue(BaseModel):
    key: str
    title: str
    assignee: str
    reporter: str
    priority: str
    status: str
    url: str

