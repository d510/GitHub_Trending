"""週次パイプライン実行スクリプト"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from collector import collect_all, save_snapshot
from keywords import aggregate_keywords, detect_changes, load_previous_keywords, save_keywords
from analyzer import analyze, save_analysis
from renderer import render_all


def main():
    print("=" * 50)
    print("GitHub Trending Analyzer - 週次パイプライン")
    print("=" * 50)

    # Step 1: データ収集
    print("\n[1/4] GitHub API データ収集...")
    snapshot = collect_all()
    save_snapshot(snapshot)

    # Step 2: キーワード分析
    print("\n[2/4] キーワード抽出・集計...")
    keywords = aggregate_keywords(snapshot)
    previous = load_previous_keywords()
    changes = detect_changes(keywords, previous)
    keywords_data = {
        "date": snapshot["collected_at"][:10],
        "keywords": keywords,
        "changes": changes,
    }
    save_keywords(keywords, changes)

    # Step 3: Claude AI分析
    print("\n[3/4] Claude AI 分析...")
    try:
        analysis = analyze(keywords_data)
        analysis_data = {"analysis": analysis}
        save_analysis(analysis)
    except Exception as e:
        print(f"  ⚠ AI分析スキップ: {e}")
        analysis_data = {"analysis": {
            "commentary": "AI分析は現在利用できません。",
            "highlights": [],
            "change_points": [],
        }}

    # Step 4: ダッシュボード生成
    print("\n[4/4] ダッシュボード生成...")
    render_all(snapshot, keywords_data, analysis_data)

    print("\n" + "=" * 50)
    print("完了! docs/index.html をブラウザで開いて確認してください。")
    print("=" * 50)


if __name__ == "__main__":
    main()
