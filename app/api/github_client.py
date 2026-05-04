import httpx

from app.core.config import settings
from app.core.state import Finding

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {settings.github_token}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_pr_diff(repo: str, pr_number: int) -> str:
    """Fetch the raw unified diff for a PR."""
    response = httpx.get(
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}",
        headers={**HEADERS, "Accept": "application/vnd.github.v3.diff"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def post_review(repo: str, pr_number: int, findings: list[Finding], summary: str) -> None:
    """Post a review with findings formatted in the body."""
    criticals = [f for f in findings if f.get("severity") == "critical"]
    event = "REQUEST_CHANGES" if criticals else "COMMENT"

    findings_md = "\n\n".join(
        f"**[{f.get('agent','?').upper()} — {f.get('severity','?').upper()}]** `{f.get('file','?')}` linha {f.get('line','?')}\n> {f.get('comment') or f.get('description') or f.get('message', '')}"
        for f in findings
        if f.get("file")
    )

    body = summary
    if findings_md:
        body = f"{summary}\n\n---\n\n## Detalhes por agente\n\n{findings_md}"

    response = httpx.post(
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews",
        headers=HEADERS,
        json={"body": body, "event": event},
        timeout=30,
    )
    response.raise_for_status()
