"""JSON→HTML ダッシュボード生成"""

import json
import shutil
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from config import DATA_DIR, DOCS_DIR, TEMPLATES_DIR


def build_latest_json(snapshot: dict, keywords_data: dict, analysis_data: dict) -> dict:
    """フロントエンド用のlatest.jsonを組み立て"""
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "snapshot": {
            "by_language": snapshot.get("by_language", {}),
            "by_topic": snapshot.get("by_topic", {}),
        },
        "keywords": {
            "overall": keywords_data.get("keywords", {}).get("overall", []),
            "by_period": keywords_data.get("keywords", {}).get("by_period", {}),
            "by_language": keywords_data.get("keywords", {}).get("by_language", {}),
            "changes": keywords_data.get("changes", {}),
        },
        "analysis": analysis_data.get("analysis", {}),
    }


def render_dashboard():
    """Jinja2テンプレートからHTMLを生成"""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("dashboard.html.j2")

    # テンプレートは静的HTML（JSでlatest.jsonを読み込む）なので変数不要
    html = template.render()

    out_path = DOCS_DIR / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"ダッシュボード生成: {out_path}")


def save_latest_json(latest: dict):
    """latest.jsonを保存"""
    out_dir = DOCS_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False)

    print(f"データ保存: {out_path}")


def copy_assets():
    """CSSなどの静的ファイルをコピー（テンプレートから生成する場合用）"""
    # style.css は docs/assets/ に直接配置済みなので通常は不要
    pass


def render_all(snapshot: dict, keywords_data: dict, analysis_data: dict):
    """全出力ファイルを生成"""
    latest = build_latest_json(snapshot, keywords_data, analysis_data)
    save_latest_json(latest)
    render_dashboard()


if __name__ == "__main__":
    # 最新の各データファイルを読み込んで生成
    snap_files = sorted((DATA_DIR / "snapshots").glob("*.json"))
    kw_files = sorted((DATA_DIR / "keywords").glob("*.json"))
    analysis_files = sorted((DATA_DIR / "analysis").glob("*.json"))

    if not snap_files or not kw_files:
        print("データファイルが不足しています。先にcollector.py, keywords.pyを実行してください。")
        raise SystemExit(1)

    with open(snap_files[-1], encoding="utf-8") as f:
        snapshot = json.load(f)
    with open(kw_files[-1], encoding="utf-8") as f:
        keywords_data = json.load(f)

    analysis_data = {}
    if analysis_files:
        with open(analysis_files[-1], encoding="utf-8") as f:
            analysis_data = json.load(f)

    print("ダッシュボード生成開始...")
    render_all(snapshot, keywords_data, analysis_data)
    print("完了!")
