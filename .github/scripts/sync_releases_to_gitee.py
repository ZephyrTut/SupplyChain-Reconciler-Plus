#!/usr/bin/env python3
"""将 GitHub Releases 迁移/同步到 Gitee Releases。"""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Dict, List

import requests


def getenv_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少必填环境变量: {name}")
    return value


def github_headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "release-migrator"
    }


def list_github_releases(repo: str, token: str, max_count: int = 0) -> List[Dict[str, Any]]:
    releases: List[Dict[str, Any]] = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/releases"
        resp = requests.get(
            url,
            headers=github_headers(token),
            params={"per_page": 100, "page": page},
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        releases.extend(batch)
        if max_count > 0 and len(releases) >= max_count:
            return releases[:max_count]
        page += 1
    return releases


def get_gitee_release_by_tag(owner: str, repo: str, token: str, tag: str) -> Dict[str, Any] | None:
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/tags/{tag}"
    resp = requests.get(url, params={"access_token": token}, timeout=60)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def create_gitee_release(owner: str, repo: str, token: str, gh_release: Dict[str, Any]) -> Dict[str, Any]:
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases"
    payload = {
        "access_token": token,
        "tag_name": gh_release.get("tag_name", ""),
        "name": gh_release.get("name") or gh_release.get("tag_name", ""),
        "body": gh_release.get("body") or "",
        "prerelease": bool(gh_release.get("prerelease", False)),
    }
    resp = requests.post(url, data=payload, timeout=60)
    # 若已存在可能返回 422，回读
    if resp.status_code in (200, 201):
        return resp.json()
    if resp.status_code == 422:
        existed = get_gitee_release_by_tag(owner, repo, token, gh_release.get("tag_name", ""))
        if existed:
            return existed
    resp.raise_for_status()
    return resp.json()


def list_gitee_asset_names(gitee_release: Dict[str, Any]) -> set[str]:
    assets = gitee_release.get("assets") or []
    names = set()
    for item in assets:
        name = item.get("name")
        if name:
            names.add(name)
    return names


def download_github_asset(asset: Dict[str, Any], token: str, target_path: str) -> None:
    url = asset.get("url")
    if not url:
        raise RuntimeError("GitHub asset 缺少 url")

    headers = github_headers(token)
    headers["Accept"] = "application/octet-stream"

    with requests.get(url, headers=headers, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def upload_gitee_asset(owner: str, repo: str, token: str, release_id: int, file_path: str) -> None:
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/{release_id}/attach_files"
    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            data={"access_token": token},
            files={"file": f},
            timeout=300,
        )
    resp.raise_for_status()


def sync_release(
    gh_release: Dict[str, Any],
    gh_token: str,
    gitee_owner: str,
    gitee_repo: str,
    gitee_token: str,
) -> None:
    tag = gh_release.get("tag_name", "")
    if not tag:
        return

    print(f"\n=== 同步 Release: {tag} ===")

    gitee_release = get_gitee_release_by_tag(gitee_owner, gitee_repo, gitee_token, tag)
    if gitee_release is None:
        print("Gitee 不存在该版本，创建中...")
        gitee_release = create_gitee_release(gitee_owner, gitee_repo, gitee_token, gh_release)
    else:
        print("Gitee 已存在该版本，执行资源补齐...")

    release_id = gitee_release.get("id")
    if release_id is None:
        raise RuntimeError(f"Gitee release 缺少 id: {tag}")

    existing_assets = list_gitee_asset_names(gitee_release)

    assets = gh_release.get("assets") or []
    if not assets:
        print("该版本无附件，跳过附件同步")
        return

    with tempfile.TemporaryDirectory(prefix="gh2gitee_") as tmp:
        for asset in assets:
            name = asset.get("name", "")
            if not name:
                continue
            if name in existing_assets:
                print(f"- 跳过已存在附件: {name}")
                continue

            print(f"- 下载并上传附件: {name}")
            local_path = os.path.join(tmp, name)
            download_github_asset(asset, gh_token, local_path)
            upload_gitee_asset(gitee_owner, gitee_repo, gitee_token, int(release_id), local_path)


def main() -> int:
    gh_repo = getenv_required("GH_REPO")
    gh_token = getenv_required("GH_TOKEN")
    gitee_owner = getenv_required("GITEE_OWNER")
    gitee_repo = getenv_required("GITEE_REPO")
    gitee_token = getenv_required("GITEE_TOKEN")

    sync_tag = os.getenv("SYNC_TAG", "").strip()
    sync_limit_raw = os.getenv("SYNC_LIMIT", "0").strip()

    try:
        sync_limit = int(sync_limit_raw) if sync_limit_raw else 0
    except ValueError:
        sync_limit = 0

    releases = list_github_releases(gh_repo, gh_token, max_count=0)
    if sync_tag:
        releases = [r for r in releases if r.get("tag_name") == sync_tag]

    if sync_limit > 0:
        releases = releases[:sync_limit]

    if not releases:
        print("未找到可同步的 GitHub Releases")
        return 0

    for release in releases:
        sync_release(release, gh_token, gitee_owner, gitee_repo, gitee_token)

    print("\n同步完成")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"同步失败: {exc}")
        raise
