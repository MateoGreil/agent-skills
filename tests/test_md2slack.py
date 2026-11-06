import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "md2slack"))

import md2slack


class ConverterTests(unittest.TestCase):
    def test_extracts_first_table_and_stops_at_prose(self):
        text = (
            "Introduction\n\n"
            "| Name | Status |\n"
            "| :--- | ---: |\n"
            "| Example | Ready |\n"
            "End of table\n\n"
            "| Other | Value |\n"
            "| --- | --- |\n"
            "| Ignored | Later |\n"
        )
        self.assertEqual(
            md2slack.extract_table(text),
            [["Name", "Status"], ["Example", "Ready"]],
        )

    def test_accepts_optional_outer_pipes_and_crlf(self):
        text = "Name | Status\r\n--- | ---\r\n Example | Ready \r\n"
        self.assertEqual(
            md2slack.extract_table(text),
            [["Name", "Status"], ["Example", "Ready"]],
        )

    def test_preserves_empty_cells(self):
        self.assertEqual(md2slack.split_cells("| Name |  | Value |"), ["Name", "", "Value"])

    def test_stops_at_blank_line(self):
        text = "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n| not | a row |"
        self.assertEqual(md2slack.extract_table(text), [["A", "B"], ["1", "2"]])

    def test_rejects_input_without_a_separator(self):
        for text in ("", "plain text", "| A | B |\n| 1 | 2 |", "| A | B |"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(SystemExit, "no Markdown table found"):
                    md2slack.extract_table(text)

    def test_inline_html_escapes_text_and_preserves_supported_formatting(self):
        self.assertEqual(
            md2slack.inline_md_to_html(
                '<tag> & [docs](https://example.invalid/?a=1&b=2) **ready** `x < y`'
            ),
            '&lt;tag&gt; &amp; <a href="https://example.invalid/?a=1&amp;b=2">docs</a> '
            '<b>ready</b> <code>x &lt; y</code>',
        )

    def test_inline_text_removes_supported_markdown(self):
        self.assertEqual(
            md2slack.inline_md_to_text("[docs](https://example.invalid) **ready** `value` café"),
            "docs ready value café",
        )

    def test_html_uses_header_and_body_rows(self):
        rows = [["Name", "Status"], ["**Example**", "`ready`"], ["<other>", ""]]
        self.assertEqual(
            md2slack.to_html(rows),
            "<table><thead><tr><th>Name</th><th>Status</th></tr></thead><tbody>"
            "<tr><td><b>Example</b></td><td><code>ready</code></td></tr>"
            "<tr><td>&lt;other&gt;</td><td></td></tr></tbody></table>",
        )

    def test_tsv_has_plain_text_tabs_and_unicode(self):
        rows = [["Name", "Link"], ["**café**", "[docs](https://example.invalid)"]]
        self.assertEqual(md2slack.to_tsv(rows), "Name\tLink\ncafé\tdocs")

    def test_header_only_table_has_empty_body(self):
        rows = md2slack.extract_table("| Name |\n| --- |")
        self.assertEqual(
            md2slack.to_html(rows),
            "<table><thead><tr><th>Name</th></tr></thead><tbody></tbody></table>",
        )
        self.assertEqual(md2slack.to_tsv(rows), "Name")

    def test_cli_writes_requested_utf8_outputs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            directory = Path(directory)
            source = directory / "input.md"
            html_output = directory / "result.html"
            tsv_output = directory / "result.tsv"
            source.write_text("| Name | State |\n| --- | --- |\n| café | **ready** |", encoding="utf-8")
            argv = [
                "md2slack.py", str(source),
                "--html-out", str(html_output), "--tsv-out", str(tsv_output),
            ]
            output = io.StringIO()
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
                md2slack.main()
            self.assertEqual(tsv_output.read_text(encoding="utf-8"), "Name\tState\ncafé\tready")
            self.assertIn("<td>café</td><td><b>ready</b></td>", html_output.read_text(encoding="utf-8"))
            self.assertIn("1 data rows ->", output.getvalue())

    def test_cli_rejects_invalid_input_without_writing_outputs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            directory = Path(directory)
            source = directory / "input.md"
            html_output = directory / "result.html"
            tsv_output = directory / "result.tsv"
            source.write_text("No table here", encoding="utf-8")
            argv = [
                "md2slack.py", str(source),
                "--html-out", str(html_output), "--tsv-out", str(tsv_output),
            ]
            with patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(SystemExit, "no Markdown table found"):
                    md2slack.main()
            self.assertFalse(html_output.exists())
            self.assertFalse(tsv_output.exists())


if __name__ == "__main__":
    unittest.main()
