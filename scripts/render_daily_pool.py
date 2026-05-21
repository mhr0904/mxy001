#!/usr/bin/env python3
"""Render the daily candidate pool to static HTML and Markdown."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TODAY_JSON = ROOT / "data" / "today.json"
INDEX_HTML = ROOT / "index.html"
TODAY_MD = ROOT / "today.md"


FIELD_LABELS = [
    ("source_platform", "来源平台"),
    ("author", "作者"),
    ("published_at", "发布时间"),
    ("original_url", "原始链接"),
    ("topic_category", "主题分类"),
    ("confidence", "置信度"),
    ("fully_read", "是否完整读取"),
    ("recommend_chatgpt_second_pass", "是否建议 ChatGPT 二次判断"),
    ("may_need_open_original", "是否可能需要我打开原文")
]


def load_today() -> dict[str, Any]:
    with TODAY_JSON.open("r", encoding="utf-8") as file:
        return json.load(file)


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " / ".join(str(item) for item in value)
    return str(value)


def clipped_excerpt(value: Any) -> str:
    value_text = text(value).strip()
    if len(value_text) <= 300:
        return value_text
    return value_text[:297] + "..."


def e(value: Any) -> str:
    return html.escape(text(value), quote=True)


def render_source_status(data: dict[str, Any]) -> str:
    items = []
    for source in data.get("source_status", []):
        platform = e(source.get("platform", ""))
        status = e(source.get("status", ""))
        method = e(source.get("collection_method", ""))
        boundary = e(source.get("boundary", ""))
        items.append(
            "      <li>"
            f"<strong>{platform}</strong>：{status}。{method} 边界：{boundary}"
            "</li>"
        )
    return "\n".join(items)


def render_rules(data: dict[str, Any], key: str) -> str:
    rules = data.get("filtering_rules", {}).get(key, [])
    return "\n".join(f"      <li>{e(rule)}</li>" for rule in rules)


def render_safety(data: dict[str, Any]) -> str:
    return "\n".join(f"      <li>{e(rule)}</li>" for rule in data.get("safety_boundaries", []))


def render_candidate_article(candidate: dict[str, Any], index: int) -> str:
    rows = []
    for key, label in FIELD_LABELS:
        value = candidate.get(key, "")
        if key == "original_url" and value:
            safe_url = e(value)
            rendered_value = f'<a href="{safe_url}">{safe_url}</a>'
        else:
            rendered_value = e(value)
        rows.append(f"      <li>{label}：{rendered_value}</li>")

    title = e(candidate.get("title", "未命名候选"))
    excerpt = e(clipped_excerpt(candidate.get("excerpt", "")))
    reason = e(candidate.get("codex_screening_reason", ""))
    return f"""  <article>
    <h2>{index}. {title}</h2>
    <ul>
{chr(10).join(rows)}
    </ul>
    <p><strong>摘录：</strong>{excerpt}</p>
    <p><strong>Codex 初筛理由：</strong>{reason}</p>
  </article>"""


def render_html(data: dict[str, Any]) -> str:
    candidates = data.get("candidates", [])
    articles = "\n\n".join(
        render_candidate_article(candidate, index)
        for index, candidate in enumerate(candidates, 1)
    )
    source_status = render_source_status(data)
    drop_rules = render_rules(data, "drop_by_default")
    priority_rules = render_rules(data, "prioritize")
    safety = render_safety(data)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{e(data.get("title", "米小鱼每日信息候选池"))}</title>
  <style>
    body {{
      color: #222;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.65;
      margin: 0 auto;
      max-width: 920px;
      padding: 32px 20px 56px;
    }}
    article {{
      border-top: 1px solid #ddd;
      padding: 20px 0;
    }}
    h1 {{
      font-size: 2rem;
      line-height: 1.25;
      margin: 0 0 12px;
    }}
    h2 {{
      font-size: 1.25rem;
      margin: 28px 0 10px;
    }}
    p, li {{
      font-size: 1rem;
    }}
    a {{
      color: #0645ad;
    }}
    .meta {{
      color: #555;
    }}
  </style>
</head>
<body>
  <h1>{e(data.get("title", "米小鱼每日信息候选池"))}</h1>
  <p><strong>{e(data.get("review_instruction", ""))}</strong></p>
  <p class="meta">目标日期：{e(data.get("target_date", ""))}；生成时间：{e(data.get("generated_at", ""))}；时区：{e(data.get("timezone", ""))}</p>
  <p>{e(data.get("data_note", ""))}</p>

  <h2>信源状态</h2>
  <ul>
{source_status}
  </ul>

  <h2>候选信息</h2>
{articles}

  <h2>默认过滤</h2>
  <ul>
{drop_rules}
  </ul>

  <h2>优先保留</h2>
  <ul>
{priority_rules}
  </ul>

  <h2>安全边界</h2>
  <ul>
{safety}
  </ul>
</body>
</html>
"""


def md_line(label: str, value: Any) -> str:
    return f"- {label}：{text(value)}"


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# {text(data.get('title', '米小鱼每日信息候选池'))}",
        "",
        text(data.get("review_instruction", "")),
        "",
        f"- 目标日期：{text(data.get('target_date', ''))}",
        f"- 生成时间：{text(data.get('generated_at', ''))}",
        f"- 时区：{text(data.get('timezone', ''))}",
        f"- 状态：{text(data.get('run_status', ''))}",
        "",
        text(data.get("data_note", "")),
        "",
        "## 信源状态",
        "",
    ]

    for source in data.get("source_status", []):
        lines.append(
            f"- {text(source.get('platform', ''))}：{text(source.get('status', ''))}。"
            f"{text(source.get('collection_method', ''))} 边界：{text(source.get('boundary', ''))}"
        )

    lines.extend(["", "## 候选信息", ""])
    for index, candidate in enumerate(data.get("candidates", []), 1):
        lines.append(f"### {index}. {text(candidate.get('title', '未命名候选'))}")
        for key, label in FIELD_LABELS:
            lines.append(md_line(label, candidate.get(key, "")))
        lines.append(f"- 摘录：{clipped_excerpt(candidate.get('excerpt', ''))}")
        lines.append(f"- Codex 初筛理由：{text(candidate.get('codex_screening_reason', ''))}")
        lines.append("")

    lines.extend(["## 默认过滤", ""])
    lines.extend(f"- {rule}" for rule in data.get("filtering_rules", {}).get("drop_by_default", []))
    lines.extend(["", "## 优先保留", ""])
    lines.extend(f"- {rule}" for rule in data.get("filtering_rules", {}).get("prioritize", []))
    lines.extend(["", "## 安全边界", ""])
    lines.extend(f"- {rule}" for rule in data.get("safety_boundaries", []))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = load_today()
    INDEX_HTML.write_text(render_html(data), encoding="utf-8")
    TODAY_MD.write_text(render_markdown(data), encoding="utf-8")


if __name__ == "__main__":
    main()
