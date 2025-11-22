import os

from tools.chat import ask_llm
from config import MD_DIR, BUILD_DB
from tools.chunking import extract_chunks_from_md
from tools.embedding import build_vector_db
from tools.search import search_chunks


# -----------------------
# 列出 Markdown 文件
# -----------------------
def list_md_files(md_dir):
    md_files = []
    for root, _, files in os.walk(md_dir):
        for name in files:
            if name.endswith(".md"):
                md_files.append(os.path.join(root, name))
    return md_files


# -----------------------
# 主循环
# -----------------------
if __name__ == "__main__":
    md_files = list_md_files(MD_DIR)

    if BUILD_DB:
        build_vector_db(md_files, extract_chunks_from_md)
        print("\033[32m向量库构建完成！\033[0m")  # 绿色
    else:
        print("\033[33m跳过向量库构建，直接使用现有库。\033[0m")  # 黄色

    try:
        print("\033[36m可以输入查询内容（输入 exit 退出）：\033[0m")  # 青色
        while True:
            query = input("\n\033[34m请输入搜索内容：\033[0m")  # 蓝色输入提示
            if query.lower() in ["exit", "quit"]:
                print("\033[31m已退出程序。\033[0m")  # 红色退出提示
                break

            context = search_chunks(query)
            # print(context)
            answer = ask_llm(query, context)
            print("\n\033[32m=== 解答 ===\033[0m")  # 绿色
            print(f"\033[92m{answer}\033[0m")  # 绿色

    finally:
        # 确保 Ollama 服务在退出时被关闭
        os.system("ollama stop gemma3:12b")
        print("\033[33mOllama 服务已关闭。\033[0m")
