"""
Download README.md files from all public repositories in the GitHub organization.
"""

import base64
import os
from pathlib import Path
from typing import Dict, List

import requests
import yaml


def fetch_org_repos(org_name: str, token: str | None = None) -> List[Dict]:
    """
    Fetch all public repositories from the GitHub organization.

    Args:
        org_name: GitHub organization name
        token: GitHub personal access token (optional, but recommended)

    Returns:
        List of repository metadata dicts
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    repos = []
    page = 1

    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos"
        params = {"type": "public", "per_page": 100, "page": page}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        page_repos = response.json()
        if not page_repos:
            break

        repos.extend(page_repos)
        page += 1

    print(f"Found {len(repos)} public repositories in {org_name}")
    return repos


def fetch_readme(repo_full_name: str, token: str = None) -> str | None:
    """
    Fetch README.md content from a repository.

    Args:
        repo_full_name: Full repository name (e.g., 'owner/repo')
        token: GitHub personal access token

    Returns:
        README content as string, or None if not found
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo_full_name}/readme"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # GitHub API returns base64 encoded content
        content = response.json().get("content", "")
        decoded = base64.b64decode(content).decode("utf-8")

        print(f"✓ Fetched README from {repo_full_name}")
        return decoded

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"✗ No README found in {repo_full_name}")
        else:
            print(f"✗ Error fetching README from {repo_full_name}: {e}")
        return None


def save_readmes(org_name: str, output_dir: Path, token: str = None):
    """
    Download all READMEs from organization and save to output directory.

    Args:
        org_name: GitHub organization name
        output_dir: Directory to save README files
        token: GitHub personal access token
    """

    # Clean output directory
    # if output_dir.exists():
    #     for file in output_dir.glob("*.md"):
    #         file.unlink()

    output_dir.mkdir(parents=True, exist_ok=True)

    repos = fetch_org_repos(org_name, token)

    saved_count = 0
    for repo in repos:
        repo_name = repo["name"]
        repo_full_name = repo["full_name"]

        readme_content = fetch_readme(repo_full_name, token)

        if readme_content:
            # Save as {repo_name}_README.md
            output_path = output_dir / f"{repo_name}_README.md"
            output_path.write_text(readme_content, encoding="utf-8")
            saved_count += 1

    print(f"\n{'=' * 60}")
    print(f"Download complete: {saved_count}/{len(repos)} READMEs saved")
    print(f"Output directory: {output_dir}")
    print(f"{'=' * 60}")


def main():
    """Main entry point"""
    params = yaml.safe_load(open("params.yaml"))

    org_name = params["org_name"]
    token = os.environ.get("GITHUB_TOKEN")
    output_dir = Path(params["output_dir"])

    print(f"Fetching READMEs from GitHub organization: {org_name}")
    print(f"Output directory: {output_dir}")
    print(f"{'=' * 60}\n")

    save_readmes(org_name, output_dir, token)


if __name__ == "__main__":
    main()
