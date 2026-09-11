import os
import re
from functools import lru_cache
from urllib.parse import urlparse

from jira import JIRA
from jira.exceptions import JIRAError


class JiraConfigError(Exception):
    """Raised when a project's JIRA URL or credentials are missing/invalid."""


class JiraApiError(Exception):
    """Raised when the JIRA API call itself fails."""


_PROJECT_KEY_PATTERNS = [
    re.compile(r"/browse/([A-Za-z]\w+)-\d+"),
    re.compile(r"/browse/([A-Za-z]\w+)/?$"),
    re.compile(r"/projects/([A-Za-z]\w+)"),
    re.compile(r"[?&]projectKey=([A-Za-z]\w+)"),
]


def parse_project_key(jira_project_url: str) -> str:
    for pattern in _PROJECT_KEY_PATTERNS:
        match = pattern.search(jira_project_url)
        if match:
            return match.group(1).upper()
    raise JiraConfigError(
        f"Could not determine a JIRA project key from URL: {jira_project_url}"
    )


def parse_server_url(jira_project_url: str) -> str:
    parsed = urlparse(jira_project_url)
    if not parsed.scheme or not parsed.netloc:
        raise JiraConfigError(f"Invalid JIRA project URL: {jira_project_url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_cloud(server_url: str) -> bool:
    return ".atlassian.net" in urlparse(server_url).netloc


@lru_cache(maxsize=8)
def _get_client(server_url: str, token: str, email: str | None) -> JIRA:
    if email:
        # Jira Cloud authenticates with email + API token via basic auth.
        return JIRA(server=server_url, basic_auth=(email, token))
    # Jira Server/Data Center uses a personal access token instead.
    return JIRA(server=server_url, token_auth=token)


def _client_for(server_url: str) -> JIRA:
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        raise JiraConfigError("JIRA_API_TOKEN environment variable is not set")
    email = os.environ.get("JIRA_EMAIL")
    if _is_cloud(server_url) and not email:
        raise JiraConfigError(
            "JIRA_EMAIL environment variable is required to authenticate with JIRA Cloud"
        )
    return _get_client(server_url, token, email)


def _serialize_issue(issue, server_url: str) -> dict:
    fields = issue.fields
    assignee = getattr(fields, "assignee", None)
    reporter = getattr(fields, "reporter", None)
    priority = getattr(fields, "priority", None)
    status = getattr(fields, "status", None)
    return {
        "key": issue.key,
        "title": fields.summary,
        "assignee": getattr(assignee, "displayName", None) if assignee else "Unassigned",
        "reporter": getattr(reporter, "displayName", None) if reporter else "Unknown",
        "priority": getattr(priority, "name", None) if priority else "None",
        "status": getattr(status, "name", None) if status else "Unknown",
        "url": f"{server_url}/browse/{issue.key}",
    }


def fetch_project_issues(jira_project_url: str) -> list[dict]:
    if not jira_project_url:
        raise JiraConfigError("Project does not have a JIRA project URL configured")

    server_url = parse_server_url(jira_project_url)
    project_key = parse_project_key(jira_project_url)

    try:
        client = _client_for(server_url)
        issues = client.search_issues(
            f'project = "{project_key}" ORDER BY updated DESC',
            maxResults=100,
            fields="summary,assignee,reporter,priority,status",
        )
    except JIRAError as exc:
        raise JiraApiError(f"JIRA API request failed: {exc.text or exc}") from exc

    return [_serialize_issue(issue, server_url) for issue in issues]
