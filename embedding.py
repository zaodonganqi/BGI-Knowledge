from sentence_transformers import SentenceTransformer
import chromadb
from config import DB_DIR, COLLECTION_NAME, BUILD_DB
import os
import json
import shutil

print("Loading embedding model...")
model = SentenceTransformer("BAAI/bge-m3")

# -----------------------
# 初始化 Chroma
# -----------------------
if BUILD_DB:
    print("构建模式：删除旧数据库并重新生成")
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)
    os.makedirs(DB_DIR, exist_ok=True)
else:
    print("非构建模式：跳过删除数据库")

client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def normalize_path(path: str):
    """将 Windows 路径标准化，让 source 看起来更短"""
    return os.path.normpath(path).replace("\\", "/")


def build_vector_db(md_files, extract_chunks_func, save_pre_embeddings=True, batch_size=5000):
    """
    构建向量数据库（分批插入，避免 Chroma 内部 batch size 限制）

    md_files: 文件列表
    extract_chunks_func: 切分函数
    save_pre_embeddings: 是否保存向量化前数据
    batch_size: 每批插入的最大数量
    """
    docs, metas, ids = [], [], []
    pre_embedding_data = []

    for path in md_files:
        norm_path = normalize_path(path)
        chunks = extract_chunks_func(path)

        for i, chunk in enumerate(chunks):
            docs.append(chunk)

            meta = {
                "source": norm_path,
                "title": chunk.split("\n")[0],
                "chunk_index": i
            }
            metas.append(meta)

            ids.append(f"{norm_path}-{i}")

            if save_pre_embeddings:
                pre_embedding_data.append({
                    "source": norm_path,
                    "title": meta["title"],
                    "chunk_index": i,
                    "text": chunk
                })

    # 保存向量化前数据
    if save_pre_embeddings:
        pre_file = os.path.join(DB_DIR, "pre_embeddings.json")
        with open(pre_file, "w", encoding="utf-8") as f:
            json.dump(pre_embedding_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(pre_embedding_data)} pre-embedding chunks to {pre_file}")

    embeddings = model.encode(docs).tolist()

    # 分批插入 Chroma
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i:i + batch_size],
            metadatas=metas[i:i + batch_size],
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size]
        )
        print(f"Inserted batch {i // batch_size + 1} ({len(docs[i:i + batch_size])} chunks)")

    print("Vector DB saved to Chroma at:", DB_DIR)
