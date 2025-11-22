import re
from config import CHUNK_SIZE, CHUNK_OVERLAP


def fix_broken_urls(text):
    """
    自动修复被错误拆开的 URL，如：
    'github. com' → 'github.com'
    '/path. html' → '/path.html'
    """
    # 修复 domain.com
    text = re.sub(r'(\w)\.\s+(\w)', r'\1.\2', text)

    # 修复 /xxx.html 等路径
    text = re.sub(r'(/[\w\-/]+)\.\s+(\w)', r'\1.\2', text)

    return text


def split_by_headings(lines):
    """
    改进点：
    1. 支持代码块整体跳过 heading 逻辑
    2. 空内容标题块直接丢弃
    3. 跳过 YAML front-matter（--- 形式）
    """
    blocks = []
    current_title = None
    current_content = []
    in_code_block = False
    in_front_matter = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        # -------------------------
        # Front-matter 处理
        # -------------------------
        if line.strip() == "---":
            in_front_matter = not in_front_matter
            continue

        if in_front_matter:
            continue  # front-matter 内容全部跳过

        # -------------------------
        # 代码块处理
        # -------------------------
        if line.startswith("```"):
            in_code_block = not in_code_block
            current_content.append(line)
            continue

        # -------------------------
        # 标题识别（不在代码块里）
        # -------------------------
        if not in_code_block and re.match(r"^#+\s", line):
            # 推入之前的 block（如果有内容）
            text = "\n".join(current_content).strip()
            if text:
                blocks.append((current_title or line, text))

            current_title = line
            current_content = []
        else:
            current_content.append(line)

    # 尾部 block
    text = "\n".join(current_content).strip()
    if text:
        blocks.append((current_title or "# (no title)", text))

    return blocks


def split_paragraphs(text):
    """
    改进点：
    1. 如果是代码块，整段返回
    2. 如果没有标题，且内容是多行正文，则整段返回
    """
    text = fix_broken_urls(text)
    stripped = text.strip()

    # 代码块无需拆分
    if stripped.startswith("```"):
        return [text]

    # 按行切
    lines = [fix_broken_urls(line.strip()) for line in text.splitlines() if line.strip()]

    # 关键增强：如果不存在代码、列表、问号结构 → 视为“多行正文”
    if len(lines) > 1:
        has_list = any(line.startswith(("*", "-", "1.", "2.", "3.")) for line in lines)
        has_faq = any(line.startswith("❓") for line in lines)
        has_heading = any(re.match(r"^#+\s", line) for line in lines)

        # 是纯正文（多行），则整体返回，不拆！
        if not has_list and not has_faq and not has_heading:
            return [text]

    return lines


def split_sentences(paragraph):
    """
    若是代码块，则不进行句子切分
    """
    paragraph = fix_broken_urls(paragraph)

    if paragraph.strip().startswith("```"):
        return [paragraph]

    # ⚠️ 避免 URL 被切割，例如：
    # https://xxx.com/aaa.bbb 不能按 "." 切
    # 用负向前瞻排除 URL
    sentences = re.split(
        r'(?<=[。！？!?])(?!\S)|(?<=[^.])\.(?!\S|[a-zA-Z0-9/_-])',
        paragraph
    )

    return [fix_broken_urls(s) for s in sentences if s.strip()]


def merge_sentences_to_chunks(title, sentences):
    """
    普通文本进行合并。
    若是代码块，则直接返回 title + text
    """
    # 若是代码块，则整段返回
    if len(sentences) == 1 and sentences[0].strip().startswith("```"):
        return [f"{title}\n{sentences[0]}"]

    chunks = []
    current_sentences = []

    for sentence in sentences:
        sentence = fix_broken_urls(sentence)
        current_text_len = (
            sum(len(s) for s in current_sentences)
            + len(current_sentences)
            + len(sentence)
        )

        if current_text_len > CHUNK_SIZE and current_sentences:
            chunks.append(f"{title}\n{' '.join(current_sentences)}")

            # Overlap
            overlap_sentences = []
            overlap_len = 0
            for s in reversed(current_sentences):
                if overlap_len + len(s) < CHUNK_OVERLAP:
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s) + 1
                else:
                    break
            current_sentences = overlap_sentences

        current_sentences.append(sentence)

    if current_sentences:
        chunks.append(f"{title}\n{' '.join(current_sentences)}")

    return chunks


def extract_chunks_from_md(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = split_by_headings(lines)
    final_chunks = []

    for title, content in blocks:
        paragraphs = split_paragraphs(content)

        for para in paragraphs:
            sentences = split_sentences(para)
            chunks = merge_sentences_to_chunks(title, sentences)
            final_chunks.extend(chunks)

    return final_chunks
