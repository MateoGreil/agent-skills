#!/usr/bin/env python3
"""Post a Markdown table as a native Slack table block via chat.postMessage.

Reads slackcli browser-session credentials from ~/.config/slackcli/workspaces.json
(kept local, never printed). Tries top-level blocks first, then attachments.

Usage: send_slack_table.py <file.md> <channel_id> [message_text]
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from md2slack import extract_table

INLINE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*")


def cell_elements(cell: str, bold: bool) -> list[dict]:
    elements = []
    pos = 0

    def add_text(text: str, style: dict | None = None) -> None:
        if not text:
            return
        el = {"type": "text", "text": text}
        merged = dict(style or {})
        if bold:
            merged["bold"] = True
        if merged:
            el["style"] = merged
        elements.append(el)

    for m in INLINE.finditer(cell):
        add_text(cell[pos:m.start()])
        link_text, link_url, code, bold_text = m.groups()
        if link_url:
            el = {"type": "link", "url": link_url, "text": link_text}
            if bold:
                el["style"] = {"bold": True}
            elements.append(el)
        elif code:
            add_text(code, {"code": True})
        else:
            add_text(bold_text, {"bold": True})
        pos = m.end()
    add_text(cell[pos:])
    return elements


def table_block(rows: list[list[str]]) -> dict:
    return {
        "type": "table",
        "rows": [
            [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": cell_elements(cell, bold=(i == 0)),
                        }
                    ],
                }
                for cell in row
            ]
            for i, row in enumerate(rows)
        ],
    }


def load_credentials() -> tuple[str, str, str]:
    cfg = json.loads(
        (Path.home() / ".config/slackcli/workspaces.json").read_text()
    )
    ws = cfg["workspaces"][cfg["default_workspace"]]
    return ws["xoxc_token"], ws["xoxd_token"], ws["workspace_url"]


def post(payload: dict, token: str, cookie: str, base_url: str) -> dict:
    form = {
        key: value if isinstance(value, str) else json.dumps(value)
        for key, value in payload.items()
    }
    form["token"] = token
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat.postMessage",
        data=urllib.parse.urlencode(form).encode(),
        headers={
            "Cookie": f"d={urllib.parse.quote(cookie, safe='')}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main() -> None:
    md_file, channel = sys.argv[1], sys.argv[2]
    text = sys.argv[3] if len(sys.argv) > 3 else "Markdown table"
    rows = extract_table(Path(md_file).read_text(encoding="utf-8"))
    block = table_block(rows)
    token, cookie, base_url = load_credentials()

    result = post(
        {"channel": channel, "text": text, "blocks": [block]}, token, cookie, base_url
    )
    if not result.get("ok"):
        print(f"top-level blocks refused ({result.get('error')}), trying attachments...")
        result = post(
            {"channel": channel, "text": text, "attachments": [{"blocks": [block]}]},
            token,
            cookie,
            base_url,
        )
    print(json.dumps({k: result.get(k) for k in ("ok", "error", "ts")}))


if __name__ == "__main__":
    main()
