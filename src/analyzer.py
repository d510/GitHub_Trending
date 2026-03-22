"""Claude API トレンド分析"""

import json
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from config import CLAUDE_MODEL, DATA_DIR, ROOT_DIR

load_dotenv(ROOT_DIR / ".env", override=True)

SYSTEM_PROMPT = """\
あなたはGitHubの技術トレンドを分析する専門家です。
提供されたデータを基に、今週のGitHub技術トレンドを日本語で分析してください。

以下のJSON形式で出力してください（JSONのみ、説明文不要）:
{
  "commentary": "全体サマリー（3〜5文で今週のトレンドを概観）",
  "highlights": [
    {
      "title": "注目ポイントのタイトル",
      "description": "2〜3文の解説",
      "sentiment": "positive / neutral / negative"
    }
  ],
  "change_points": [
    {
      "keyword": "キーワード名",
      "direction": "up / down / new",
      "explanation": "なぜこのトレンドが来ているのかの考察（1〜2文）"
    }
  ]
}"""


def build_prompt(keywords_data: dict) -> str:
    """分析用プロンプトを構築"""
    keywords = keywords_data.get("keywords", {})
    changes = keywords_data.get("changes", {})

    sections = []

    # 全体キーワードランキング
    overall = keywords.get("overall", [])
    if overall:
        top20 = overall[:20]
        lines = [f"  {kw}: {count}" for kw, count in top20]
        sections.append("■ 全体キーワードランキング (上位20)\n" + "\n".join(lines))

    # 期間別比較
    by_period = keywords.get("by_period", {})
    for period in ["week", "month", "year"]:
        if period in by_period:
            top10 = by_period[period][:10]
            lines = [f"  {kw}: {count}" for kw, count in top10]
            sections.append(f"■ {period}のトップキーワード\n" + "\n".join(lines))

    # 言語別トップキーワード
    by_lang = keywords.get("by_language", {})
    for lang, kws in by_lang.items():
        top5 = kws[:5]
        lines = [f"  {kw}: {count}" for kw, count in top5]
        sections.append(f"■ {lang} のトップキーワード\n" + "\n".join(lines))

    # 変化点
    if changes.get("rising"):
        lines = [f"  {r['keyword']}: {r['prev_count']}→{r['count']} ({r['ratio']}x)"
                 for r in changes["rising"][:10]]
        sections.append("■ 急上昇キーワード\n" + "\n".join(lines))

    if changes.get("new"):
        lines = [f"  {r['keyword']}: {r['count']}" for r in changes["new"][:10]]
        sections.append("■ 新出キーワード\n" + "\n".join(lines))

    if changes.get("falling"):
        lines = [f"  {r['keyword']}: {r['prev_count']}→{r['count']} ({r['ratio']}x)"
                 for r in changes["falling"][:10]]
        sections.append("■ 下降キーワード\n" + "\n".join(lines))

    return f"今週のGitHubトレンドデータ（{keywords_data.get('date', '不明')}）:\n\n" + "\n\n".join(sections)


def analyze(keywords_data: dict) -> dict:
    """Claude APIでトレンド分析を実行"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = build_prompt(keywords_data)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # トークン使用量をログ出力
    usage = message.usage
    print(f"  トークン使用量: 入力={usage.input_tokens}, 出力={usage.output_tokens}")
    cost = (usage.input_tokens * 0.80 + usage.output_tokens * 4.00) / 1_000_000
    print(f"  推定コスト: ${cost:.4f} (約{cost * 150:.1f}円)")

    response_text = message.content[0].text

    # JSONパース（コードブロックで囲まれている場合も対応）
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


def save_analysis(analysis: dict) -> str:
    """分析結果を保存"""
    out_dir = DATA_DIR / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output = {
        "date": date_str,
        "analysis": analysis,
    }

    out_path = out_dir / f"{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"分析結果保存: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    # 最新のキーワードファイルを読み込んで分析
    kw_dir = DATA_DIR / "keywords"
    files = sorted(kw_dir.glob("*.json"))
    if not files:
        print("キーワードファイルが見つかりません。先に keywords.py を実行してください。")
        raise SystemExit(1)

    with open(files[-1], encoding="utf-8") as f:
        keywords_data = json.load(f)

    print("Claude API 分析開始...")
    analysis = analyze(keywords_data)
    path = save_analysis(analysis)

    print(f"\n=== 分析結果 ===")
    print(f"サマリー: {analysis.get('commentary', '')[:200]}")
    print(f"注目ポイント: {len(analysis.get('highlights', []))}件")
    print(f"変化点: {len(analysis.get('change_points', []))}件")
    print(f"\n完了: {path}")
