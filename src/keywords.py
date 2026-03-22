"""キーワード抽出・正規化・変化点検出"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, STOP_WORDS, SYNONYMS


def _tokenize(text: str) -> list[str]:
    """テキストを小文字トークンに分割"""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def _normalize(word: str) -> str:
    """同義語辞書で正規化"""
    w = word.lower()
    for canonical, variants in SYNONYMS.items():
        if w in variants or w == canonical.lower():
            return canonical
    return word


def extract_keywords(repos: list[dict]) -> Counter:
    """リポジトリ群からキーワードを抽出・集計"""
    counter = Counter()

    for repo in repos:
        # topics をそのまま利用（GitHub が付与した公式タグ）
        for topic in repo.get("topics", []):
            normalized = _normalize(topic)
            counter[normalized] += 1

        # description からトークン抽出
        tokens = _tokenize(repo.get("description", ""))
        for token in tokens:
            normalized = _normalize(token)
            counter[normalized] += 1

    return counter


def aggregate_keywords(snapshot: dict) -> dict:
    """スナップショット全体からキーワードを集計"""
    result = {"by_language": {}, "by_period": {}, "by_topic": {}, "overall": {}}

    all_repos_set = set()
    all_repos = []
    period_repos = {}

    # 言語別
    for lang, periods in snapshot.get("by_language", {}).items():
        lang_repos = []
        for period_name, repos in periods.items():
            lang_repos.extend(repos)
            # 期間別にも集計
            if period_name not in period_repos:
                period_repos[period_name] = []
            period_repos[period_name].extend(repos)

        result["by_language"][lang] = extract_keywords(lang_repos).most_common(30)

        for r in lang_repos:
            if r["full_name"] not in all_repos_set:
                all_repos_set.add(r["full_name"])
                all_repos.append(r)

    # 期間別
    for period_name, repos in period_repos.items():
        # 重複除去
        seen = set()
        unique = []
        for r in repos:
            if r["full_name"] not in seen:
                seen.add(r["full_name"])
                unique.append(r)
        result["by_period"][period_name] = extract_keywords(unique).most_common(30)

    # トピック別
    for topic, repos in snapshot.get("by_topic", {}).items():
        result["by_topic"][topic] = extract_keywords(repos).most_common(20)
        for r in repos:
            if r["full_name"] not in all_repos_set:
                all_repos_set.add(r["full_name"])
                all_repos.append(r)

    # 全体
    result["overall"] = extract_keywords(all_repos).most_common(50)

    return result


def detect_changes(current: dict, previous: dict | None) -> dict:
    """前週比で急上昇・新出キーワードを検出"""
    if previous is None:
        return {"rising": [], "new": [], "falling": []}

    curr = dict(current.get("overall", []))
    prev = dict(previous.get("overall", []))

    rising = []
    new_kw = []
    falling = []

    for kw, count in curr.items():
        if kw not in prev:
            new_kw.append({"keyword": kw, "count": count})
        elif prev[kw] > 0 and count / prev[kw] >= 2.0:
            rising.append({
                "keyword": kw,
                "count": count,
                "prev_count": prev[kw],
                "ratio": round(count / prev[kw], 2),
            })

    for kw, count in prev.items():
        if kw in curr and count > 0 and curr[kw] / count <= 0.5:
            falling.append({
                "keyword": kw,
                "count": curr.get(kw, 0),
                "prev_count": count,
                "ratio": round(curr.get(kw, 0) / count, 2),
            })

    rising.sort(key=lambda x: x["ratio"], reverse=True)
    new_kw.sort(key=lambda x: x["count"], reverse=True)
    falling.sort(key=lambda x: x["ratio"])

    return {
        "rising": rising[:15],
        "new": new_kw[:15],
        "falling": falling[:15],
    }


def load_previous_keywords() -> dict | None:
    """直前のキーワードファイルを読み込み"""
    kw_dir = DATA_DIR / "keywords"
    if not kw_dir.exists():
        return None
    files = sorted(kw_dir.glob("*.json"))
    if not files:
        return None
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def save_keywords(data: dict, changes: dict) -> str:
    """キーワード集計結果を保存"""
    out_dir = DATA_DIR / "keywords"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output = {
        "date": date_str,
        "keywords": data,
        "changes": changes,
    }

    out_path = out_dir / f"{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"キーワード保存: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    # 最新のスナップショットを読み込んでキーワード抽出
    snap_dir = DATA_DIR / "snapshots"
    files = sorted(snap_dir.glob("*.json"))
    if not files:
        print("スナップショットが見つかりません。先に collector.py を実行してください。")
        raise SystemExit(1)

    with open(files[-1], encoding="utf-8") as f:
        snapshot = json.load(f)

    print("キーワード抽出開始...")
    keywords = aggregate_keywords(snapshot)
    previous = load_previous_keywords()
    changes = detect_changes(keywords, previous)
    path = save_keywords(keywords, changes)

    print(f"\nトップキーワード:")
    for kw, count in keywords["overall"][:20]:
        print(f"  {kw}: {count}")

    if changes["rising"]:
        print(f"\n急上昇:")
        for item in changes["rising"][:5]:
            print(f"  {item['keyword']}: {item['prev_count']}→{item['count']} ({item['ratio']}x)")

    print(f"\n完了: {path}")
