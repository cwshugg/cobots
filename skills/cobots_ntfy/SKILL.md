---
name: cobots-ntfy-cli
description: CLI for sending push notifications via ntfy.sh.
---

# ntfy-cli

A CLI skill for sending push notifications via [ntfy.sh](https://ntfy.sh).

## Description

This skill provides subcommands to send notifications to an ntfy.sh topic, send a test
notification to verify configuration, and display the current ntfy settings from the
cobots workspace. It wraps the shared `cobots_lib.ntfy.client` library.

## Configuration

The ntfy settings are stored in the `ntfy` section of `cobots-config.yaml`:

```yaml
ntfy:
  url: "https://ntfy.sh"
  topic: "my-cobots-topic"
  token: "tk_AgXXXXXXXXXXXX"
```

| Field | Default | Required | Description |
|---|---|---|---|
| `url` | `https://ntfy.sh` | No | The ntfy server base URL. |
| `topic` | `""` (empty) | Yes (for sending) | The ntfy topic to publish to. |
| `token` | `""` (empty) | No | Optional Bearer access token for authenticated topics. |

Use the cobots workspace CLI to initialize the workspace if it hasn't already been set up.

## Usage

```bash
# Send a notification with a message.
python ntfy-cli.py send --message "Build completed successfully" --title "CI"

# Send with priority and tags.
python ntfy-cli.py send -m "Disk usage at 95%" -t "Warning" -p high --tags "warning"

# Send a Markdown-formatted notification.
python ntfy-cli.py send -m "**Task done!** See [results](https://example.com)" --markdown

# Read message from STDIN.
echo "Deployment finished" | python ntfy-cli.py send --title "Deploy"

# Override topic and server URL.
python ntfy-cli.py send -m "Hello" --topic "other-topic" --url "https://my-ntfy.example.com"

# Send a test notification to verify configuration.
python ntfy-cli.py test

# Send a test notification to a specific topic.
python ntfy-cli.py test --topic "my-test-topic"

# Display the current ntfy configuration.
python ntfy-cli.py show-config
```

## Subcommands

### `send`

Publishes a notification to the configured ntfy topic.

* `--message` / `-m` — Message body. If omitted, reads from STDIN.
* `--title` / `-t` *(optional)* — Notification title.
* `--priority` / `-p` *(optional)* — Priority: 1–5 or name (min, low, default, high, max, urgent).
* `--tags` *(optional)* — Comma-separated list of tags.
* `--click` *(optional)* — URL to open when the notification is clicked.
* `--markdown` *(optional)* — Flag to enable Markdown rendering.
* `--topic` *(optional)* — Override the topic from config.
* `--url` *(optional)* — Override the server URL from config.
* `--token` *(optional)* — Override the auth token from config.

If both `--message` and STDIN are empty, the command exits with an error.

**Output (success):** `Sent: <message_id>` to stdout, exit 0.

**Output (failure):** `Error: <description>` to stderr, exit 1.

### `test`

Sends a predefined test notification to verify the ntfy configuration.

* `--topic` *(optional)* — Override the topic from config.
* `--url` *(optional)* — Override the server URL from config.
* `--token` *(optional)* — Override the auth token from config.

The test notification uses:
- Message: "Cobots ntfy test notification"
- Title: "Cobots Test"
- Tags: white_check_mark

### `show-config`

Displays the resolved ntfy settings from the workspace configuration.

The token is masked for security (first 5 characters + "..." if set).

```
ntfy configuration:
  url:   https://ntfy.sh
  topic: my-cobots-topic
  token: tk_Ag... (set)
```

## Return Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Error (missing config, network failure, invalid args, etc.) |

## Library Usage

Other skills can import and use the notification client directly:

```python
from cobots_lib.workspace.working_dir import load_config
from cobots_lib.ntfy.client import send_notification

config = load_config()
result = send_notification(config, "Task completed!", title="Cobots", tags=["tada"])
if result.success:
    print(f"Sent: {result.message_id}")
else:
    print(f"Error: {result.error}")
```

For more control, use `NtfyClient` directly:

```python
from cobots_lib.ntfy.client import NtfyClient

client = NtfyClient(url="https://ntfy.sh", topic="my-topic", token="tk_...")
result = client.send("Custom notification", priority=4, tags=["warning"])
```
