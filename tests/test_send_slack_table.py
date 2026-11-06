import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import call, patch
import urllib.error
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "md2slack"))

import send_slack_table as sender

CREDENTIALS = ("dummy-token", "dummy cookie/+%", "https://workspace.example.invalid/")
TABLE = "| Name | Status |\n| --- | --- |\n| Example | **Ready** |"
INPUT = ROOT / "tests" / "dummy-table.md"
DUMMY_HOME = ROOT / "tests" / "dummy-home"
PATH_READ_TEXT = Path.read_text


class SenderTests(unittest.TestCase):
    def setUp(self):
        for patcher in (
            patch.object(sender.urllib.request, "urlopen", side_effect=AssertionError("Unexpected network call")),
            patch.object(Path, "home", return_value=DUMMY_HOME),
            patch.object(Path, "read_text", side_effect=AssertionError("Unexpected file or credential read")),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, responses, text=None, table=TABLE):
        argv = ["send_slack_table.py", str(INPUT), "C_DUMMY"]
        if text is not None:
            argv.append(text)
        output = io.StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(Path, "read_text", autospec=PATH_READ_TEXT, return_value=table) as read_text,
            patch.object(sender, "load_credentials", return_value=CREDENTIALS) as credentials,
            patch.object(sender, "post", side_effect=responses) as post,
            contextlib.redirect_stdout(output),
        ):
            sender.main()
        read_text.assert_called_once_with(INPUT, encoding="utf-8")
        credentials.assert_called_once_with()
        self.assertNotIn(CREDENTIALS[0], output.getvalue())
        self.assertNotIn(CREDENTIALS[1], output.getvalue())
        return post, output.getvalue()

    def test_cell_elements_preserve_inline_styles_and_links(self):
        self.assertEqual(
            sender.cell_elements("plain [docs](https://example.invalid) `value` **ready**!", bold=False),
            [
                {"type": "text", "text": "plain "},
                {"type": "link", "url": "https://example.invalid", "text": "docs"},
                {"type": "text", "text": " "},
                {"type": "text", "text": "value", "style": {"code": True}},
                {"type": "text", "text": " "},
                {"type": "text", "text": "ready", "style": {"bold": True}},
                {"type": "text", "text": "!"},
            ],
        )

    def test_header_bold_is_merged_with_inline_code_and_links(self):
        self.assertEqual(
            sender.cell_elements("`code` [docs](https://example.invalid)", bold=True),
            [
                {"type": "text", "text": "code", "style": {"code": True, "bold": True}},
                {"type": "text", "text": " ", "style": {"bold": True}},
                {"type": "link", "url": "https://example.invalid", "text": "docs", "style": {"bold": True}},
            ],
        )

    def test_empty_cell_has_no_spurious_elements(self):
        self.assertEqual(sender.cell_elements("", bold=True), [])

    def test_table_block_contains_rich_text_cells_and_only_header_is_bold(self):
        block = sender.table_block([["Name", "Status"], ["Example", "Ready"]])
        self.assertEqual(block["type"], "table")
        self.assertEqual([len(row) for row in block["rows"]], [2, 2])
        self.assertEqual(
            block["rows"][0][0],
            {"type": "rich_text", "elements": [
                {"type": "rich_text_section", "elements": [
                    {"type": "text", "text": "Name", "style": {"bold": True}}
                ]}
            ]},
        )
        self.assertEqual(
            block["rows"][1][0]["elements"][0]["elements"],
            [{"type": "text", "text": "Example"}],
        )

    def test_credentials_select_the_default_workspace_using_only_mocked_reads(self):
        config = {
            "default_workspace": "selected",
            "workspaces": {
                "other": {"xoxc_token": "unused"},
                "selected": dict(zip(("xoxc_token", "xoxd_token", "workspace_url"), CREDENTIALS)),
            },
        }
        with patch.object(Path, "read_text", autospec=PATH_READ_TEXT, return_value=json.dumps(config)) as read_text:
            self.assertEqual(sender.load_credentials(), CREDENTIALS)
        read_text.assert_called_once_with(DUMMY_HOME / ".config" / "slackcli" / "workspaces.json")

    def test_credentials_missing_default_workspace_raise(self):
        with patch.object(Path, "read_text", return_value=json.dumps({"workspaces": {}})):
            with self.assertRaises(KeyError):
                sender.load_credentials()

    def test_credentials_malformed_json_raises(self):
        with patch.object(Path, "read_text", return_value="not json"):
            with self.assertRaises(json.JSONDecodeError):
                sender.load_credentials()

    def test_post_encodes_native_block_payload_and_browser_cookie(self):
        payload = {"channel": "C_DUMMY", "text": "Example & café", "blocks": [sender.table_block([["Name"]])]}
        response = {"ok": True, "ts": "123.456"}
        with patch.object(sender.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as open_url:
            self.assertEqual(sender.post(payload, *CREDENTIALS), response)
        open_url.assert_called_once()
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://workspace.example.invalid/api/chat.postMessage")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/x-www-form-urlencoded")
        self.assertEqual(request.get_header("Cookie"), "d=" + urllib.parse.quote(CREDENTIALS[1], safe=""))
        form = urllib.parse.parse_qs(request.data.decode())
        self.assertEqual(form["token"], [CREDENTIALS[0]])
        self.assertEqual(form["channel"], ["C_DUMMY"])
        self.assertEqual(form["text"], ["Example & café"])
        self.assertEqual(json.loads(form["blocks"][0]), payload["blocks"])

    def test_post_encodes_attachments_as_json(self):
        attachments = [{"blocks": [sender.table_block([["Name"]])]}]
        with patch.object(sender.urllib.request, "urlopen", return_value=io.BytesIO(b'{"ok": true}')) as open_url:
            sender.post({"channel": "C_DUMMY", "attachments": attachments}, *CREDENTIALS)
        form = urllib.parse.parse_qs(open_url.call_args.args[0].data.decode())
        self.assertEqual(json.loads(form["attachments"][0]), attachments)

    def test_post_propagates_http_errors(self):
        error = urllib.error.HTTPError("https://workspace.example.invalid", 503, "Unavailable", None, None)
        with patch.object(sender.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(urllib.error.HTTPError):
                sender.post({"channel": "C_DUMMY"}, *CREDENTIALS)

    def test_post_rejects_malformed_json_response(self):
        with patch.object(sender.urllib.request, "urlopen", return_value=io.BytesIO(b"not json")):
            with self.assertRaises(json.JSONDecodeError):
                sender.post({"channel": "C_DUMMY"}, *CREDENTIALS)

    def test_main_default_intro_is_neutral_and_success_does_not_fallback(self):
        post, output = self.run_main([{"ok": True, "ts": "123.456"}])
        block = sender.table_block([["Name", "Status"], ["Example", "**Ready**"]])
        post.assert_called_once_with(
            {"channel": "C_DUMMY", "text": "Markdown table", "blocks": [block]}, *CREDENTIALS
        )
        self.assertEqual(json.loads(output), {"ok": True, "error": None, "ts": "123.456"})

    def test_main_preserves_custom_and_explicitly_empty_intro(self):
        for text in ("Example summary", ""):
            with self.subTest(text=text):
                post, _ = self.run_main([{"ok": True}], text=text)
                self.assertEqual(post.call_args.args[0]["text"], text)

    def test_main_retries_rejected_blocks_as_attachments_with_identical_table(self):
        post, output = self.run_main([
            {"ok": False, "error": "invalid_blocks"},
            {"ok": True, "ts": "123.456"},
        ], text="Example summary")
        block = sender.table_block([["Name", "Status"], ["Example", "**Ready**"]])
        self.assertEqual(post.call_args_list, [
            call({"channel": "C_DUMMY", "text": "Example summary", "blocks": [block]}, *CREDENTIALS),
            call({"channel": "C_DUMMY", "text": "Example summary", "attachments": [{"blocks": [block]}]}, *CREDENTIALS),
        ])
        self.assertIn("top-level blocks refused (invalid_blocks), trying attachments...", output)
        self.assertEqual(json.loads(output.splitlines()[-1]), {"ok": True, "error": None, "ts": "123.456"})

    def test_main_reports_attachment_failure_without_claiming_success_or_retrying_again(self):
        post, output = self.run_main([
            {"ok": False, "error": "invalid_blocks"},
            {"ok": False, "error": "invalid_auth"},
        ])
        self.assertEqual(post.call_count, 2)
        self.assertEqual(json.loads(output.splitlines()[-1]), {"ok": False, "error": "invalid_auth", "ts": None})

    def test_main_transport_error_propagates_without_attachment_retry(self):
        with (
            patch.object(sys, "argv", ["send_slack_table.py", str(INPUT), "C_DUMMY"]),
            patch.object(Path, "read_text", return_value=TABLE),
            patch.object(sender, "load_credentials", return_value=CREDENTIALS),
            patch.object(sender, "post", side_effect=OSError("Dummy transport failure")) as post,
        ):
            with self.assertRaisesRegex(OSError, "Dummy transport failure"):
                sender.main()
        self.assertEqual(post.call_count, 1)

    def test_main_invalid_table_does_not_load_credentials_or_post(self):
        with (
            patch.object(sys, "argv", ["send_slack_table.py", str(INPUT), "C_DUMMY"]),
            patch.object(Path, "read_text", return_value="No table here"),
            patch.object(sender, "load_credentials") as credentials,
            patch.object(sender, "post") as post,
        ):
            with self.assertRaisesRegex(SystemExit, "no Markdown table found"):
                sender.main()
        credentials.assert_not_called()
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
