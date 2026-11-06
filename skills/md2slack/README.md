# Markdown table helpers for Slack

This directory pairs an agent workflow with three Python programs. They provide a GTK clipboard route for Linux and a separate HTTP route for posting a table message. Installation and agent-specific linking are described in the [package README](../../README.md).

## Program interfaces

### `md2slack.py`

```text
python3 md2slack.py INPUT.md [--html-out OUTPUT.html] [--tsv-out OUTPUT.tsv]
```

The converter locates the first pipe-delimited Markdown table with a separator row. It writes an HTML header/body table and a tab-delimited text representation, defaulting to `table.html` and `table.tsv` in the working directory. Supported inline links, double-asterisk bold and backtick code become HTML markup; the TSV output keeps their text without the formatting markers.

Parsing is deliberately limited: cells are split on pipe characters rather than processed by a general Markdown engine. For example, an escaped pipe inside a cell is not treated specially.

### `clip_table.py`

```text
python3 clip_table.py INPUT.html INPUT.tsv
```

This Linux helper reads the generated files and registers a GTK4 content provider with three MIME types: `text/html`, `text/plain;charset=utf-8` and `text/plain`. The HTML representation and the TSV representation are available simultaneously. Its event loop keeps the clipboard provider active; stopping the program or copying something else ends its ability to serve that table.

Python >=3.10, PyGObject, GTK4 and an X11/Wayland session are required. On Ubuntu the GTK bindings come from `python3-gi` and `gir1.2-gtk-4.0`. There is no macOS backend in this package.

### `send_slack_table.py`

```text
python3 send_slack_table.py INPUT.md CHANNEL_OR_DM_ID [INTRO_TEXT]
```

The sender uses the converter's table extraction and constructs a Slack `table` payload containing rich-text cells. Header styling and inline links, bold and code are represented in the cell elements. The optional introduction defaults to `Markdown table`.

It reads the default workspace's browser-session credentials from the user's local slackcli configuration, then submits a form-encoded request to that workspace's `chat.postMessage` endpoint. A rejected top-level `blocks` response triggers one request using attachment blocks. The final stdout JSON includes `ok`, `error` and `ts`; HTTP or JSON-decoding exceptions may terminate the program instead. Credentials and authenticated workspace configuration are not distributed with these files.

The converter and sender need Python >=3.10 and use the standard library. The clipboard helper additionally needs the Linux GTK dependencies above; no npm runtime packages are required.

## Workflow boundaries

Follow [SKILL.md](SKILL.md) for input authorization, destination confirmation, invocation paths and delivery checks. It permits conversation tables and explicitly designated input files, not clipboard harvesting or unrelated file discovery. Without a confirmed recipient the workflow prepares a paste; direct posting also requires the user's publishing request. Resolve all three executable paths from the skill's own directory.

The offline tests mock Slack requests and credential reads. They do not authenticate, send messages or take clipboard ownership.

## Credit and licensing

Credit for the original macOS clipboard idea belongs to [loslcrd/md2slack](https://github.com/loslcrd/md2slack). That project's pandoc/AppleScript implementation and its documentation are not bundled here. These instructions and this README were written for the interfaces of the Linux/API programs in this directory.

The upstream repository has no declared license. No license has been selected for this package either; its `UNLICENSED` metadata is not an MIT grant or a replacement for upstream terms. The credit above acknowledges the idea, not permission to redistribute upstream material.
