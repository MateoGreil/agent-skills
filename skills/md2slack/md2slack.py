#!/usr/bin/env python3
"""Convert the first Markdown table of a file to HTML + TSV for Slack paste.

Slack turns a pasted text/html <table> into a native table block.
Usage: md2slack.py <file.md> [--html-out out.html] [--tsv-out out.tsv]
"""
import argparse
import html
import re
import sys

SEPARATOR_ROW = re.compile(r"^\s*\|?[\s\-:|]+\|?\s*$")


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def extract_table(text: str) -> list[list[str]]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "|" not in line or i + 1 >= len(lines):
            continue
        if SEPARATOR_ROW.match(lines[i + 1]) and "|" in lines[i + 1]:
            rows = [split_cells(line)]
            for row_line in lines[i + 2:]:
                if "|" not in row_line or not row_line.strip():
                    break
                rows.append(split_cells(row_line))
            return rows
    sys.exit("Error: no Markdown table found in input")


def inline_md_to_html(cell: str) -> str:
    out = html.escape(cell, quote=False)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return out


def inline_md_to_text(cell: str) -> str:
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    out = re.sub(r"\*\*([^*]+)\*\*", r"\1", out)
    out = re.sub(r"`([^`]+)`", r"\1", out)
    return out


def to_html(rows: list[list[str]]) -> str:
    head = "".join(f"<th>{inline_md_to_html(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{inline_md_to_html(c)}</td>" for c in row) + "</tr>"
        for row in rows[1:]
    )
    return (
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def to_tsv(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(inline_md_to_text(c) for c in row) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--html-out", default="table.html")
    parser.add_argument("--tsv-out", default="table.tsv")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = extract_table(f.read())

    with open(args.html_out, "w", encoding="utf-8") as f:
        f.write(to_html(rows))
    with open(args.tsv_out, "w", encoding="utf-8") as f:
        f.write(to_tsv(rows))
    print(f"{len(rows) - 1} data rows -> {args.html_out}, {args.tsv_out}")


if __name__ == "__main__":
    main()
