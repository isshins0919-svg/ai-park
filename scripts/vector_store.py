#!/usr/bin/env python3
"""vector_store.py -- Knowledge Vector Store for VOYAGE号

knowledge/ 全ファイルをチャンク→ベクトル化→SQLiteに永続保存。
スキルからセマンティック検索でナレッジを引ける基盤。

Usage:
    python3 scripts/vector_store.py index              # 全ファイルindex
    python3 scripts/vector_store.py search "query"     # セマンティック検索
    python3 scripts/vector_store.py search "query" -k 3  # top_k指定
    python3 scripts/vector_store.py status             # 統計表示
"""

import argparse, json, os, re, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# === Paths ===
BASE = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE / ".claude" / "knowledge"
DB_PATH = Path(__file__).resolve().parent / "knowledge_vectors.db"
EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DELAY = 0.35  # seconds between API calls

# === Category Map ===
CATEGORY_MAP = {
    "pak-philosophy.md": "philosophy",
    "sawada-article-lp-philosophy.md": "philosophy",
    "ccdd-strategy.md": "strategy",
    "hook-db.md": "db",
    "cta-db.md": "db",
    "bgm-catalog.md": "db",
    "banner-dna-templates.md": "db",
    "shortad-dna-templates.md": "db",
    "amazon-algorithm.md": "technical",
    "vector-utils.md": "technical",
    "google-slides-recipe.md": "technical",
    "telop-platform-guidelines.md": "technical",
}
DB_FILES = {"hook-db.md", "cta-db.md", "bgm-catalog.md", "banner-dna-templates.md"}

# === Gemini Client ===
_client = None

def _load_env(var):
    if os.environ.get(var):
        return
    # .zshrc から export VAR="value" or export VAR=value を抽出
    for rc in [Path.home() / ".zshrc", Path.home() / ".zshenv"]:
        if not rc.exists():
            continue
        try:
            for line in rc.read_text().splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                m = re.match(rf'export\s+{var}=["\']?([^"\'#\s]+)["\']?', line)
                if m:
                    os.environ[var] = m.group(1)
                    return
        except Exception:
            pass

def _get_client():
    global _client
    if _client is None:
        _load_env("GEMINI_API_KEY_1")
        key = os.environ.get("GEMINI_API_KEY_1")
        if not key:
            print("ERROR: GEMINI_API_KEY_1 not found", file=sys.stderr)
            sys.exit(1)
        from google import genai
        _client = genai.Client(api_key=key)
    return _client

def embed(text):
    client = _get_client()
    r = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0

# === Chunking ===

def _get_category(filename):
    return CATEGORY_MAP.get(filename, "guide")

def chunk_by_h2(content, filename):
    """## 見出し単位でチャンク分割"""
    chunks = []
    # H1タイトルを取得
    h1_match = re.match(r"^#\s+(.+)", content)
    h1_title = h1_match.group(1).strip() if h1_match else filename

    # ## で分割
    sections = re.split(r"\n(?=## )", content)
    idx = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue
        # 見出しを取得
        heading_match = re.match(r"^##\s+(.+)", section)
        if heading_match:
            heading = heading_match.group(1).strip()
        elif section.startswith("# "):
            heading = h1_title
        else:
            heading = h1_title

        # 短すぎるセクション（見出しだけ等）はスキップ
        text = section.strip()
        if len(text) < 30:
            continue

        # 長すぎるセクション（800文字超）は空行で再分割
        if len(text) > 800:
            sub_parts = re.split(r"\n\n+", text)
            buffer = ""
            sub_heading = heading
            for part in sub_parts:
                if len(buffer) + len(part) > 600 and buffer:
                    chunks.append({"heading": sub_heading, "text": buffer.strip(), "chunk_index": idx})
                    idx += 1
                    buffer = part
                    # サブ見出しがあれば更新
                    sub_h = re.match(r"^###\s+(.+)", part)
                    if sub_h:
                        sub_heading = f"{heading} > {sub_h.group(1).strip()}"
                else:
                    buffer = buffer + "\n\n" + part if buffer else part
            if buffer.strip() and len(buffer.strip()) >= 30:
                chunks.append({"heading": sub_heading, "text": buffer.strip(), "chunk_index": idx})
                idx += 1
        else:
            chunks.append({"heading": heading, "text": text, "chunk_index": idx})
            idx += 1

    return chunks

def chunk_by_entry(content, filename):
    """テーブル行単位でチャンク分割（DB系ファイル用）"""
    chunks = []
    idx = 0
    current_section = filename

    for line in content.split("\n"):
        # セクション見出しを追跡
        h_match = re.match(r"^#{1,3}\s+(.+)", line)
        if h_match:
            current_section = h_match.group(1).strip()
            continue

        # テーブルヘッダー行を取得
        if line.startswith("| #") or line.startswith("| #"):
            headers = [h.strip() for h in line.split("|")[1:-1]]
            continue

        # セパレータ行をスキップ
        if re.match(r"^\|[-\s|]+\|$", line):
            continue

        # データ行
        if line.startswith("|") and not line.startswith("|---"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3:
                # セクション名 + 行内容をテキスト化
                text = f"{current_section}: {', '.join(cols)}"
                heading = cols[1] if len(cols) > 1 else cols[0]
                # **太字** を除去
                heading = re.sub(r"\*\*(.+?)\*\*", r"\1", heading)
                chunks.append({"heading": heading, "text": text, "chunk_index": idx})
                idx += 1

    return chunks

def chunk_file(filepath):
    content = filepath.read_text(encoding="utf-8")
    filename = filepath.name
    category = _get_category(filename)

    if filename in DB_FILES:
        chunks = chunk_by_entry(content, filename)
    else:
        chunks = chunk_by_h2(content, filename)

    for c in chunks:
        c["category"] = category
    return chunks

# === Database ===

def init_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT NOT NULL,
            heading     TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text        TEXT NOT NULL,
            vector      BLOB NOT NULL,
            category    TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            UNIQUE(file_path, chunk_index)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_meta (
            file_path   TEXT PRIMARY KEY,
            mtime       REAL NOT NULL,
            chunk_count INTEGER NOT NULL,
            indexed_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def get_changed_files(conn):
    """mtime比較で変更されたファイルだけ返す"""
    existing = {}
    for row in conn.execute("SELECT file_path, mtime FROM file_meta"):
        existing[row[0]] = row[1]

    changed = []
    for f in sorted(KNOWLEDGE_DIR.glob("*.md")):
        rel = f.name
        current_mtime = f.stat().st_mtime
        if rel not in existing or abs(existing[rel] - current_mtime) > 0.01:
            changed.append(f)
    return changed

def store_chunks(conn, file_path, chunks):
    now = datetime.now(timezone.utc).isoformat()
    # 古いチャンクを削除
    conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
    # 新しいチャンクを挿入
    for c in chunks:
        vec_blob = np.array(c["vector"], dtype=np.float32).tobytes()
        conn.execute(
            "INSERT INTO chunks (file_path, heading, chunk_index, text, vector, category, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (file_path, c["heading"], c["chunk_index"], c["text"], vec_blob, c["category"], now),
        )
    # file_meta更新
    mtime = (KNOWLEDGE_DIR / file_path).stat().st_mtime
    conn.execute(
        "INSERT OR REPLACE INTO file_meta (file_path, mtime, chunk_count, indexed_at) VALUES (?, ?, ?, ?)",
        (file_path, mtime, len(chunks), now),
    )
    conn.commit()

def search_vectors(conn, query_vec, top_k=5):
    q = np.array(query_vec, dtype=np.float32)
    rows = conn.execute("SELECT file_path, heading, text, vector, category FROM chunks").fetchall()
    if not rows:
        return []

    results = []
    for file_path, heading, text, vec_blob, category in rows:
        v = np.frombuffer(vec_blob, dtype=np.float32)
        sim = cosine_sim(q, v)
        results.append({
            "file": file_path,
            "heading": heading,
            "text": text[:300],  # 検索結果では300文字まで
            "similarity": round(sim, 4),
            "category": category,
        })

    results.sort(key=lambda x: -x["similarity"])
    return results[:top_k]

def get_stats(conn):
    total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    total_files = conn.execute("SELECT COUNT(*) FROM file_meta").fetchone()[0]
    categories = conn.execute(
        "SELECT category, COUNT(*) FROM chunks GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    last_indexed = conn.execute(
        "SELECT MAX(indexed_at) FROM file_meta"
    ).fetchone()[0]
    return {
        "total_chunks": total_chunks,
        "total_files": total_files,
        "last_indexed": last_indexed,
        "categories": {c: n for c, n in categories},
    }

# === CLI Commands ===

def cmd_index(args):
    conn = init_db()
    if args.force:
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM file_meta")
        conn.commit()
        files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    else:
        files = get_changed_files(conn)

    if not files:
        print("All files up to date. No indexing needed.")
        return

    print(f"Indexing {len(files)} file(s)...")
    total_chunks = 0
    for filepath in files:
        filename = filepath.name
        chunks = chunk_file(filepath)
        if not chunks:
            print(f"  SKIP {filename} (no chunks)")
            continue

        print(f"  {filename}: {len(chunks)} chunks", end="", flush=True)
        for c in chunks:
            c["vector"] = embed(c["text"])
            time.sleep(EMBED_DELAY)
            print(".", end="", flush=True)
        print(" done")

        store_chunks(conn, filename, chunks)
        total_chunks += len(chunks)

    conn.close()
    print(f"\nIndexed {len(files)} files, {total_chunks} chunks total.")

def cmd_search(args):
    conn = init_db()
    stats = get_stats(conn)
    if stats["total_chunks"] == 0:
        print('{"error": "No indexed data. Run: python3 scripts/vector_store.py index"}')
        conn.close()
        return

    query = args.query
    query_vec = embed(query)
    results = search_vectors(conn, query_vec, top_k=args.top_k)
    conn.close()

    output = {"query": query, "results": []}
    for i, r in enumerate(results):
        output["results"].append({"rank": i + 1, **r})

    print(json.dumps(output, ensure_ascii=False, indent=2))

def cmd_status(args):
    conn = init_db()
    stats = get_stats(conn)
    conn.close()

    print(f"Knowledge Vector Store")
    print(f"  DB: {DB_PATH}")
    print(f"  Files: {stats['total_files']}")
    print(f"  Chunks: {stats['total_chunks']}")
    print(f"  Last indexed: {stats['last_indexed'] or 'never'}")
    if stats["categories"]:
        print(f"  Categories:")
        for cat, count in stats["categories"].items():
            print(f"    {cat}: {count}")

# === Main ===

def main():
    parser = argparse.ArgumentParser(description="Knowledge Vector Store for VOYAGE号")
    sub = parser.add_subparsers(dest="command")

    p_index = sub.add_parser("index", help="Index knowledge files")
    p_index.add_argument("--force", "-f", action="store_true", help="Re-index all files")

    p_search = sub.add_parser("search", help="Semantic search")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--top_k", "-k", type=int, default=5, help="Number of results")

    sub.add_parser("status", help="Show store statistics")

    args = parser.parse_args()
    if args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
