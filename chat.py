import requests
import subprocess
import time

from config import OLLAMA_URL, OLLAMA_MODEL, LLM_PROMPT

# ---------------------------
# Ollama 进程管理
# ---------------------------
_ollama_process = None
_ollama_started_by_app = False


def _start_ollama_if_needed():
    """
    如果用户本地已经在运行 ollama serve，则不会重复启动。
    如果没有，则自动启动并在程序退出时关闭。
    """
    global _ollama_process, _ollama_started_by_app

    # 1. 尝试检查 Ollama 是否已运行
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
        return  # 已在运行
    except:
        pass

    # 2. 启动 Ollama 服务
    print("🔄 正在启动本地 Ollama 服务器...")
    _ollama_process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    _ollama_started_by_app = True

    # 3. 等待 Ollama 就绪
    for _ in range(40):
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
            break
        except:
            time.sleep(0.25)
    else:
        raise RuntimeError("❌ 启动 Ollama 失败，请检查是否已安装")

    # 4. 自动 pull 模型
    print(f"📥 正在检查/拉取模型 {OLLAMA_MODEL}...")
    subprocess.run(["ollama", "pull", OLLAMA_MODEL], stdout=subprocess.DEVNULL)


# ---------------------------
# LLM 调用
# ---------------------------
def ask_llm(query: str, context: str) -> str:
    """向 LLM 询问答案，包含上下文。"""

    # 确保 Ollama 启动
    _start_ollama_if_needed()

    prompt = LLM_PROMPT.format(context=context, query=query)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            # 你要的其他参数也可以加
        }
    }

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()

        answer = data.get("response")
        if answer is None:
            return f"LLM 返回异常结构: {data}"
        return answer

    except Exception as e:
        return f"LLM 调用失败: {e}"
