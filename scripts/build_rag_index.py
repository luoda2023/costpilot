"""
造价通 - 批量构建 RAG 知识库索引

扫描 config.yaml knowledge_sources 中的目录, 把所有支持的文件:
  1. 提取文本
  2. 切块
  3. 嵌入并入库 ChromaDB

特性:
  - 进度持久化: 已处理文件记录在 data/chroma/.processed.json
  - 断点续跑: 跳过已处理且 mtime 未变的文件
  - 出错容错: 单文件失败不中断整体

用法:
  python scripts/build_rag_index.py [--reset] [--limit N] [--dry-run]

依赖:
  pip install chromadb sentence-transformers
  (首次自动下载 BAAI/bge-m3 模型约 2GB)
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.server.config import get_config
from packages.server.ai.chunking import iter_chunks_from_file, extract_text
from packages.server.ai.rag import add_chunks, count, reset

SUPPORTED_EXT = {"md", "txt", "markdown", "yml", "yaml", "csv", "json", "log", "docx", "xlsx", "xls", "pdf"}
PROGRESS_FILE = PROJECT_ROOT / "data" / "chroma" / ".processed.json"


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_files(sources):
    """遍历所有源目录, 产出 (path, source_meta)"""
    for src in sources:
        root = Path(src["path"])
        if not root.exists():
            print(f"  [WARN] 路径不存在,跳过: {root}")
            continue
        allowed_exts = {e.lower().lstrip(".") for e in src.get("file_types", [])} or SUPPORTED_EXT
        skip_dirs = set(src.get("skip_dirs", []) + ["临时", "temp", "~$", ".git", "__pycache__"])
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            # 跳过黑名单目录
            if any(part in skip_dirs for part in p.parts):
                continue
            ext = p.suffix.lower().lstrip(".")
            if ext not in allowed_exts and ext not in SUPPORTED_EXT:
                continue
            yield p, src


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空已有索引,从头开始")
    parser.add_argument("--limit", type=int, default=0, help="限制处理文件数(0=不限)")
    parser.add_argument("--dry-run", action="store_true", help="只扫不算,看会处理多少文件")
    args = parser.parse_args()

    print("=" * 60)
    print("造价通 - 批量构建 RAG 知识库索引")
    print("=" * 60)

    cfg = get_config()
    print(f"\n[配置]")
    print(f"  嵌入模型: {cfg.rag.embedding_model}")
    print(f"  块大小:   {cfg.rag.chunk_size} / overlap {cfg.rag.chunk_overlap}")
    print(f"  持久化目录: {PROJECT_ROOT / cfg.rag.chroma_dir}")
    print(f"  源目录:")
    for s in cfg.knowledge_sources:
        print(f"    - {s.get('path')} | {s.get('description','')}")

    # 重置
    if args.reset:
        print("\n[RESET] 清空已有索引...")
        try:
            reset()
            progress = {}
            save_progress(progress)
            print("  [OK] 已清空")
        except RuntimeError as e:
            print(f"  [FAIL] {e}")
            return

    progress = load_progress()
    print(f"\n[断点] 已处理 {len(progress)} 个文件")

    # 扫描
    print(f"\n[扫描] 开始遍历源目录...")
    file_iter = iter_files(cfg.knowledge_sources)
    total = 0
    processed = 0
    failed = 0
    total_chunks = 0
    start = datetime.now()

    for path, src in file_iter:
        if args.limit and processed >= args.limit:
            print(f"\n[STOP] 已达 --limit {args.limit}")
            break
        total += 1
        try:
            stat = path.stat()
            mtime = int(stat.st_mtime)
            size = stat.st_size
        except Exception:
            continue

        key = str(path)
        rec = progress.get(key)
        if rec and rec.get("mtime") == mtime and rec.get("size") == size:
            continue  # 已处理且未变化

        if args.dry_run:
            print(f"  [DRY] {path}")
            processed += 1
            continue

        try:
            chunks = iter_chunks_from_file(path)
            if not chunks:
                progress[key] = {"mtime": mtime, "size": size, "chunks": 0, "skipped": True}
                continue
            n = add_chunks(chunks)
            total_chunks += n
            processed += 1
            progress[key] = {"mtime": mtime, "size": size, "chunks": n}
            # 每 20 个文件保存一次进度
            if processed % 20 == 0:
                save_progress(progress)
                print(f"  [PROG] 已处理 {processed} 文件 / {total_chunks} 块 / 当前: {path.name}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {path}: {e}")
            progress[key] = {"mtime": mtime, "size": size, "error": str(e)[:200]}

    save_progress(progress)
    elapsed = (datetime.now() - start).total_seconds()
    final_count = count()

    print()
    print("=" * 60)
    print("扫描完成")
    print("=" * 60)
    print(f"  扫描文件总数:   {total}")
    print(f"  本次处理:       {processed}")
    print(f"  失败:           {failed}")
    print(f"  本次新增块数:   {total_chunks}")
    print(f"  索引总块数:     {final_count}")
    print(f"  耗时:           {elapsed:.1f}s")
    print(f"  进度文件:       {PROGRESS_FILE}")


if __name__ == "__main__":
    main()
