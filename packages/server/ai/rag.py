"""
造价通 - RAG 知识库嵌入与检索

依赖(用户需自行安装):
  pip install chromadb sentence-transformers

向量模型: BAAI/bge-m3 (中英双语, 1024 维, 本地运行无需 API)
向量库:   ChromaDB 持久化在 data/chroma/

设计要点:
  1. 离线嵌入(sentence-transformers),无需 API
  2. 持久化,跨次启动复用
  3. 文件入库去重(基于 path + mtime)
  4. 混合检索: 语义相似 + SQL 价格库结构化查询
"""
from pathlib import Path
from typing import List, Dict, Optional, Any

from packages.server.config import get_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = PROJECT_ROOT / get_config().rag.chroma_dir
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "costpilot_kb"

_chroma_client = None
_collection = None
_embedder = None


def _ensure_components():
    global _chroma_client, _collection, _embedder
    if _collection is not None and _embedder is not None:
        return

    try:
        import chromadb
    except ImportError:
        raise RuntimeError("未安装 chromadb。请运行: pip install chromadb")

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise RuntimeError("未安装 sentence-transformers。请运行: pip install sentence-transformers")

    cfg = get_config().rag
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"},
        )
    if _embedder is None:
        _embedder = SentenceTransformer(cfg.embedding_model)


def embed_texts(texts):
    _ensure_components()
    return _embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def add_chunks(chunks):
    """chunks: [{id, text, metadata}, ...]"""
    _ensure_components()
    if not chunks:
        return 0
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c.get("metadata", {}) for c in chunks]
    embeddings = embed_texts(texts)
    _collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    return len(chunks)


def search(query, top_k=None, where=None):
    """语义检索,返回 [{id, text, metadata, score}, ...]"""
    _ensure_components()
    cfg = get_config().rag
    k = top_k or cfg.top_k
    q_vec = embed_texts([query])[0]
    results = _collection.query(query_embeddings=[q_vec], n_results=k, where=where)
    out = []
    for i in range(len(results["ids"][0])):
        score = 1 - results["distances"][0][i]
        if score < cfg.score_threshold:
            continue
        out.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] or {},
            "score": round(float(score), 4),
        })
    return out


def count():
    _ensure_components()
    return _collection.count()


def delete_by_source(source_path):
    _ensure_components()
    _collection.delete(where={"source": source_path})


def reset():
    global _collection
    _ensure_components()
    _chroma_client.delete_collection(COLLECTION_NAME)
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"},
    )


if __name__ == "__main__":
    print("=" * 60)
    print("RAG 检索模块 - 自检")
    print("=" * 60)
    try:
        _ensure_components()
        print("OK: chromadb + sentence-transformers 已就绪")
        print(f"   当前索引块数: {count()}")
    except RuntimeError as e:
        print("WARN: 依赖未就绪:")
        print(str(e))
