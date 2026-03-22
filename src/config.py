"""設定値・定数管理"""

from pathlib import Path

# プロジェクトルート
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
TEMPLATES_DIR = ROOT_DIR / "templates"

# GitHub API
GITHUB_API_BASE = "https://api.github.com"
GITHUB_SEARCH_REPOS = f"{GITHUB_API_BASE}/search/repositories"
RESULTS_PER_PAGE = 100

# 対象言語
LANGUAGES = ["Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "C++"]

# 期間定義（日数）
PERIODS = {
    "week": 7,
    "month": 30,
    "year": 365,
}

# トピック検索（言語横断）
TOPICS = [
    "llm",
    "generative-ai",
    "machine-learning",
    "web-framework",
    "devtools",
]

# キーワード同義語辞書（正規化用）
# キー: 正規化後の名前、値: 同義語リスト
SYNONYMS = {
    "LLM": ["llm", "large-language-model", "large language model", "large-language-models"],
    "AI": ["artificial-intelligence", "artificial intelligence"],
    "GenAI": ["generative-ai", "generative ai", "gen-ai", "genai"],
    "ML": ["machine-learning", "machine learning", "ml"],
    "Deep Learning": ["deep-learning", "deep learning", "dl"],
    "RAG": ["rag", "retrieval-augmented-generation", "retrieval augmented generation"],
    "Agent": ["ai-agent", "ai agent", "ai-agents", "agentic", "agent"],
    "ChatBot": ["chatbot", "chat-bot", "conversational-ai"],
    "Transformer": ["transformer", "transformers"],
    "Diffusion": ["diffusion", "stable-diffusion", "diffusion-model"],
    "CLI": ["cli", "command-line", "command line", "terminal"],
    "API": ["api", "rest-api", "restful", "graphql"],
    "Web Framework": ["web-framework", "web framework", "webapp"],
    "DevOps": ["devops", "dev-ops", "cicd", "ci-cd"],
    "Container": ["docker", "container", "kubernetes", "k8s"],
}

# ストップワード（キーワード抽出時に除外）
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "are",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "this", "that",
    "these", "those", "i", "you", "he", "she", "we", "they", "my", "your",
    "his", "her", "its", "our", "their", "not", "no", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "just", "about", "above", "after", "again",
    "also", "any", "because", "before", "between", "during", "into",
    "new", "now", "only", "own", "same", "so", "then", "up", "out",
    "over", "under", "using", "used", "use", "based", "build", "built",
    "simple", "easy", "fast", "lightweight", "powerful", "modern",
    "open", "source", "open-source", "project", "library", "tool",
    "application", "app", "written", "made", "like", "via", "way",
}

# Claude API
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
