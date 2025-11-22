from tools.embedding import model, collection
from config import TOP_K

from pathlib import Path


def format_source(path: str) -> str:
    """
    将 knowledge_resources 中的路径格式化为可读来源
    js 脚本：返回 js/目录名
    官网文档：返回 https://bettergi.com/... 地址
    """
    p = Path(path)
    parts = p.parts

    # 寻找 knowledge_resources 位置
    try:
        idx = parts.index("knowledge_resources")
    except ValueError:
        return path  # 不在 knowledge_resources 下就直接返回原路径

    # 判断类型
    if parts[idx + 1] == "js":
        # js 脚本：取下一层目录作为脚本名
        script_name = parts[idx + 2] if len(parts) > idx + 2 else "unknown-script"
        return f"js/{script_name}"
    elif parts[idx + 1] == "official":
        # 官网文档：转换为 https://bettergi.com/ 后面的路径
        url_parts = list(parts[idx + 2:-1]) + [p.stem]  # 转成 list 再拼接
        url_path = "/".join(url_parts) + ".html"
        return f"https://bettergi.com/{url_path}"
    else:
        # 其他情况直接返回原路径
        return path


def search_chunks(query, k=TOP_K):
    """
    在已有 Chroma 向量库中搜索相关文档块。

    参数:
        query (str): 用户查询内容
        k (int): 返回的最大条数

    返回:
        str: top-k chunks 拼接成的上下文
    """
    q_embed = model.encode([query]).tolist()
    results = collection.query(query_embeddings=q_embed, n_results=k)

    returned_docs = results["documents"][0] if results["documents"] else []
    returned_metas = results["metadatas"][0] if results["metadatas"] else []

    chunks = []
    for i in range(len(returned_docs)):
        text = returned_docs[i]
        meta = returned_metas[i] if i < len(returned_metas) else {}
        raw_source = meta.get("source", "unknown")
        source = format_source(raw_source)

        chunks.append(f"[来源] {source}\n{text}")

    if not chunks:
        chunks.append("未检索到相关内容。")

    return "\n\n".join(chunks)