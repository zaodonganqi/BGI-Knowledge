import os
import shutil
import subprocess
import tempfile

REPO_JS_URL = "https://github.com/babalae/bettergi-scripts-list.git"
REPO_OFFICIAL_URL = "https://github.com/huiyadanli/bettergi-docs.git"

TARGET_JS = "knowledge_resources/js"
TARGET_OFFICIAL = "knowledge_resources/official"

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"


def run(cmd, cwd=None):
    """运行命令并输出实时日志"""
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def safe_rmdir(path):
    """安全删除目录"""
    if os.path.exists(path):
        print(f"[REMOVE] {path}")
        shutil.rmtree(path)


def copy_dir(src, dst):
    """复制目录，完全覆盖"""
    safe_rmdir(dst)
    print(f"[COPY] {src} -> {dst}")
    shutil.copytree(src, dst)


def update_js():
    """任务1：拉取 bettergi-scripts-list 中的 repo/js 到 knowledge_resources/js"""
    print("\n=== 更新 js 脚本资源 ===")
    with tempfile.TemporaryDirectory() as tmp:
        run(["git", "clone", "--depth", "1", REPO_JS_URL, tmp])
        src_path = os.path.join(tmp, "repo", "js")
        if not os.path.isdir(src_path):
            raise FileNotFoundError(f"{src_path} 不存在，repo结构可能变化")
        copy_dir(src_path, TARGET_JS)
    print("[OK] js 更新完成")


def update_official():
    """任务2：拉取 bettergi-docs 的 src，删除 dev，然后复制到 official"""
    print("\n=== 更新 official 文档资源 ===")
    with tempfile.TemporaryDirectory() as tmp:
        run(["git", "clone", "--depth", "1", REPO_OFFICIAL_URL, tmp])
        src_path = os.path.join(tmp, "src")
        if not os.path.isdir(src_path):
            raise FileNotFoundError(f"{src_path} 不存在，repo结构可能变化")

        # 删除 src/dev
        dev_path = os.path.join(src_path, "dev")
        if os.path.exists(dev_path):
            print(f"[REMOVE] {dev_path}")
            shutil.rmtree(dev_path)

        # 删除 src/.vuepress
        dev_path = os.path.join(src_path, ".vuepress")
        if os.path.exists(dev_path):
            print(f"[REMOVE] {dev_path}")
            shutil.rmtree(dev_path)

        # 删除 src/assets
        dev_path = os.path.join(src_path, "assets")
        if os.path.exists(dev_path):
            print(f"[REMOVE] {dev_path}")
            shutil.rmtree(dev_path)

        copy_dir(src_path, TARGET_OFFICIAL)

    print("[OK] official 更新完成")


if __name__ == "__main__":
    print("======== 开始更新 ========")
    update_js()
    update_official()
    print("======== 全部完成 ========")
