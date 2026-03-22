"""GitHub Search API データ収集"""

import json
import os
import time
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from config import (
    DATA_DIR,
    GITHUB_SEARCH_REPOS,
    LANGUAGES,
    PERIODS,
    RESULTS_PER_PAGE,
    ROOT_DIR,
    TOPICS,
)

load_dotenv(ROOT_DIR / ".env", override=True)


def _headers():
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _wait_for_rate_limit(response: requests.Response):
    """レート制限に達した場合、リセットまで待機"""
    remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
    if remaining <= 1:
        reset_at = int(response.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset_at - int(time.time()), 1) + 1
        print(f"  レート制限接近。{wait}秒待機...")
        time.sleep(wait)
    else:
        time.sleep(2)  # 安全マージン


def search_repos(language: str | None, period_name: str, period_days: int) -> list[dict]:
    """指定言語・期間でスター数上位リポジトリを取得"""
    since = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")

    q_parts = [f"created:>{since}"]
    if language:
        q_parts.append(f"language:{language}")

    params = {
        "q": " ".join(q_parts),
        "sort": "stars",
        "order": "desc",
        "per_page": RESULTS_PER_PAGE,
    }

    resp = requests.get(GITHUB_SEARCH_REPOS, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()

    _wait_for_rate_limit(resp)

    data = resp.json()
    repos = []
    for item in data.get("items", []):
        repos.append({
            "full_name": item["full_name"],
            "description": item.get("description", ""),
            "language": item.get("language", ""),
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "topics": item.get("topics", []),
            "created_at": item["created_at"],
            "url": item["html_url"],
        })

    return repos


def search_by_topic(topic: str, period_days: int) -> list[dict]:
    """トピック指定でリポジトリを取得"""
    since = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")

    params = {
        "q": f"topic:{topic} created:>{since}",
        "sort": "stars",
        "order": "desc",
        "per_page": RESULTS_PER_PAGE,
    }

    resp = requests.get(GITHUB_SEARCH_REPOS, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()

    _wait_for_rate_limit(resp)

    data = resp.json()
    repos = []
    for item in data.get("items", []):
        repos.append({
            "full_name": item["full_name"],
            "description": item.get("description", ""),
            "language": item.get("language", ""),
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "topics": item.get("topics", []),
            "created_at": item["created_at"],
            "url": item["html_url"],
        })

    return repos


def collect_all() -> dict:
    """全言語・全期間・全トピックのデータを一括取得"""
    result = {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "by_language": {},
        "by_topic": {},
    }

    # 言語別収集
    for lang in LANGUAGES:
        result["by_language"][lang] = {}
        for period_name, period_days in PERIODS.items():
            print(f"  収集中: {lang} / {period_name} ({period_days}日)")
            repos = search_repos(lang, period_name, period_days)
            result["by_language"][lang][period_name] = repos
            print(f"    → {len(repos)}件取得")

    # トピック別収集（直近1ヶ月のみ）
    for topic in TOPICS:
        print(f"  収集中: topic={topic} / month")
        repos = search_by_topic(topic, PERIODS["month"])
        result["by_topic"][topic] = repos
        print(f"    → {len(repos)}件取得")

    return result


def save_snapshot(data: dict) -> str:
    """スナップショットをJSON保存"""
    out_dir = DATA_DIR / "snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    out_path = out_dir / f"{date_str}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"スナップショット保存: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    print("GitHub Trending データ収集開始...")
    data = collect_all()
    path = save_snapshot(data)
    print(f"完了: {path}")
