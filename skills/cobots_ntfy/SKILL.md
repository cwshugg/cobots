---
name: cobots-ntfy-cli
description: CLI for sending push notifications via ntfy.sh.
---

# ntfy-cli

A CLI skill for sending push notifications via [ntfy.sh](https://ntfy.sh).

## Description

This skill provides subcommands to send notifications to an ntfy.sh topic, send a test
notification to verify configuration, list available predefined message keys, and display
the current ntfy settings from the cobots workspace. It wraps the shared
`cobots_lib.ntfy.client` library.

## Configuration

The ntfy settings are stored in the `ntfy` section of `cobots-config.yaml`:

```yaml
ntfy:
  url: "https://ntfy.sh"
  topic: "my-cobots-topic"
  token: "tk_AgXXXXXXXXXXXX"
  mode: "confidential"
```

| Field | Default | Required | Description |
|---|---|---|---|
| `url` | `https://ntfy.sh` | No | The ntfy server base URL. |
| `topic` | `""` (empty) | Yes (for sending) | The ntfy topic to publish to. |
| `token` | `""` (empty) | No | Optional Bearer access token for authenticated topics. |
| `mode` | `"confidential"` | No | Notification mode: `open`, `confidential`, or `closed`. |
| `confidential_messages` | (none) | No | Optional list of custom message key/text pairs for confidential mode. |
| `confidential_titles` | (none) | No | Optional list of custom title key/text pairs for confidential mode. |

Use the cobots workspace CLI to initialize the workspace if it hasn't already been set up.

### Notification Modes

The `mode` field controls what messages the ntfy skill is allowed to send:

| Mode | Behavior |
|---|---|
| `open` | Any message content is allowed. No restrictions. |
| `confidential` | Only predefined messages (selected by key) are allowed for the message body. If a title is provided, it must also be a predefined title key. Free-form text is rejected. This prevents leaking sensitive project data through notifications. |
| `closed` | All notifications are refused. No messages are sent. |

The default mode is **`confidential`**.

### Custom Confidential Messages

In `confidential` mode, the skill uses a set of hardcoded predefined messages by default.
You can override these by adding a `confidential_messages` list to the config:

```yaml
ntfy:
  mode: "confidential"
  confidential_messages:
    - key: "deploy_ready"
      message: "Ready for deployment"
    - key: "ci_passed"
      message: "CI pipeline passed"
```

If `confidential_messages` is absent from the config, the hardcoded defaults are used.

### Custom Confidential Titles

Similarly, notification titles in `confidential` mode are restricted to predefined title
keys. You can override the defaults by adding a `confidential_titles` list to the config:

```yaml
ntfy:
  mode: "confidential"
  confidential_titles:
    - key: "ci_update"
      title: "CI Update"
    - key: "deploy_alert"
      title: "Deployment Alert"
```

If `confidential_titles` is absent from the config, the hardcoded defaults are used.
If no title is provided when sending, that is allowed — titles are optional.

## Usage

```bash
# Send a notification (open mode: free-form message).
python ntfy-cli.py send --message "Build completed successfully" --title "CI"

# Send a notification (confidential mode: use message and title keys).
python ntfy-cli.py send --message task_done --title task_update

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

# List available predefined message keys.
python ntfy-cli.py list-messages

# List available predefined title keys.
python ntfy-cli.py list-titles

# Display the current ntfy configuration.
python ntfy-cli.py show-config
```

## Subcommands

### `send`

Publishes a notification to the configured ntfy topic.

* `--message` / `-m` — Message body (open mode) or message key (confidential mode). If omitted, reads from STDIN.
* `--title` / `-t` *(optional)* — Notification title (open mode) or title key (confidential mode).
* `--priority` / `-p` *(optional)* — Priority: 1–5 or name (min, low, default, high, max, urgent).
* `--tags` *(optional)* — Comma-separated list of tags.
* `--click` *(optional)* — URL to open when the notification is clicked.
* `--markdown` *(optional)* — Flag to enable Markdown rendering.
* `--topic` *(optional)* — Override the topic from config.
* `--url` *(optional)* — Override the server URL from config.
* `--token` *(optional)* — Override the auth token from config.

If both `--message` and STDIN are empty, the command exits with an error.

**Mode behavior:**

- **open** — `--message` accepts any free-form text. `--title` accepts any free-form text.
- **confidential** — `--message` must be a valid predefined message key (e.g. `task_done`). `--title`, if provided, must be a valid predefined title key (e.g. `task_update`). If an invalid key is given, the error output includes all available keys and their text.
- **closed** — The command exits with an error explaining notifications are disabled.

**Output (success):** `Sent: <message_id>` to stdout, exit 0.

**Output (failure):** `Error: <description>` to stderr, exit 1.

### `test`

Sends a predefined test notification to verify the ntfy configuration.

* `--topic` *(optional)* — Override the topic from config.
* `--url` *(optional)* — Override the server URL from config.
* `--token` *(optional)* — Override the auth token from config.

In **open** mode, the test notification uses a free-form message. In **confidential** mode, it uses the `task_done` predefined key. In **closed** mode, the command exits with an error.

### `list-messages`

Prints all available predefined message keys and their display text. Uses custom messages from config if set, otherwise the hardcoded defaults.

```
Available message keys:
  build_done → Build completed
  build_failed → Build failed
  build_started → Build started
  deploy_done → Deployment completed
  deploy_failed → Deployment failed
  deploy_started → Deployment started
  error_occurred → An error occurred
  pipeline_done → Pipeline completed
  pipeline_started → Pipeline started
  question_for_human → A cobot has a question for you
  report_ready → A report is ready for review
  review_done → Code review completed
  review_requested → Code review requested
  task_blocked → A task is blocked
  task_done → A task has been completed
  task_started → A task has been started
  tests_failed → Tests failed
  tests_passed → All tests passed
  waiting_for_input → Waiting for human input
```

### `list-titles`

Prints all available predefined title keys and their display text. Uses custom titles from config if set, otherwise the hardcoded defaults.

```
Available title keys:
  build_update → Build Update
  deploy_update → Deployment Update
  error_alert → Error Alert
  general → Notification
  pipeline_update → Pipeline Update
  question → Question
  report → Report
  review_update → Review Update
  task_update → Task Update
  test_update → Test Update
```

### `show-config`

Displays the resolved ntfy settings from the workspace configuration.

The token is masked for security (first 5 characters + "..." if set).

```
ntfy configuration:
  url:   https://ntfy.sh
  topic: my-cobots-topic
  token: tk_Ag... (set)
  mode:  confidential
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
result = send_notification(config, "task_done", title="task_update", tags=["tada"])
if result.success:
    print(f"Sent: {result.message_id}")
else:
    print(f"Error: {result.error}")
```

For more control, use `NtfyClient` directly:

```python
from cobots_lib.ntfy.client import NtfyClient

# Open mode — any message and title allowed
client = NtfyClient(url="https://ntfy.sh", topic="my-topic", token="tk_...", mode="open")
result = client.send("Custom notification", title="Alert", priority=4, tags=["warning"])

# Confidential mode (default) — only predefined keys allowed
client = NtfyClient(url="https://ntfy.sh", topic="my-topic")
result = client.send("task_done", title="task_update")  # resolves keys to display strings
```
