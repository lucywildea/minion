---
name: minion
description: Use when installing, configuring, operating, or troubleshooting Minion web monitors and one-off research runs.
version: 1.0.0
author: lugenx
---

# Minion

Install and operate Minion, a standalone CLI and TUI for one-off web research and scheduled YAML monitors. Handle machine actions directly when permitted. Ask the user only for decisions, credentials, or access you cannot obtain safely.

## Source of truth

Use the current repository code and live `minion ... --help` output. Do not rely on old issues, commits, remembered flags, or a previously installed version when they disagree.

Repository: `https://github.com/lugenx/minion`

For installation, updates, daemon operation, or troubleshooting, read [`references/setup.md`](references/setup.md).

## Hermes integration

The official Hermes integration consists of this normal user skill and the web provider in `integrations/hermes`. It uses the Minion binary installed on the operating system. It does not install or maintain a second Minion copy.

After obtaining approval for installation, configuration, and restart actions:

1. Install or update Minion by following [`references/setup.md`](references/setup.md).
2. Verify `minion --version` and `minion --help`.
3. Install this skill into the user's normal Hermes skills directory:
   `hermes skills install https://raw.githubusercontent.com/lugenx/minion/main/integrations/hermes/skills/minion/SKILL.md --name minion`
4. Install and enable the provider:
   `hermes plugins install lugenx/minion/integrations/hermes --enable`
5. Select the provider:
   `hermes config set web.search_backend minion`
6. Restart Hermes, begin a new session, and verify one real `web_search` call.

The provider runs synchronous inline searches without `do`, so ordinary Hermes searches do not require an LLM call from Minion. It parses Minion's native multi-document YAML output. Valid records remain usable when another source fails.

## Choose the right mode

- **One-off task:** use an inline run. It is synchronous, skips persistent deduplication, and emits a YAML document stream on stdout.
- **Recurring monitor:** create a saved YAML file, test it, then schedule it.
- **Interactive editing:** use the TUI when a human wants to inspect or edit monitors visually.

Prefer an inline run first when validating a source or prompt. Do not create a persistent monitor for a one-time request.

## Inline runs

```bash
minion run from.url="https://example.com"
minion run from.search="release announcements" from.limit=5 do="Find official releases on this page."
```

Without `do`, Minion returns sanitized source content with no LLM call. With `do`, it returns final `title`, `url`, and `summary` fields. Multiple results are separated by `---` and must be parsed as a YAML stream, not as one mapping.

Source-local options apply to the source immediately before them:

```bash
minion run from.url="https://example.com/releases" from.follow="/release/" from.render=true
```

Use live `minion run --help` and the repository README for the supported key list.

## Saved monitors

Saved configs live in `~/.config/minion/minions/*.yaml`. Build the smallest pipeline that meets the request:

```yaml
name: Release Monitor
enabled: true
when: daily @ 09:00
from:
  - url: https://example.com/releases
    follow: /release/
keep:
  - release
do: Find official product releases on this page.
tell:
  - file: ~/.config/minion/data/releases.yaml
    capacity: 100
settings:
  timeout: 15
```

Use `follow`, not a guessed URL pattern. Inspect real links before setting it. Test source retrieval before enabling delivery or scheduling.

```bash
minion run monitor_name
minion up monitor_name
minion list
minion log monitor_name
minion down monitor_name
```

`minion run monitor_name` queues the saved monitor through the daemon. Inline runs and saved monitors have different state semantics; do not use one as proof of the other's deduplication behavior.

## Credentials

Never print, paste into chat, or expose `~/.config/minion/.env`. Let the user enter secrets privately through the TUI or their local environment. If credentials already exist, use Minion without reading them. Omit `do` when no LLM is needed.

## Verification

After any setup or change, verify the exact path used:

1. `minion --version`
2. Run a harmless source test.
3. Parse stdout as YAML when using inline mode.
4. For saved monitors, confirm `minion list` state and inspect `minion log NAME`.
5. Confirm the destination received the expected record; command success alone is not delivery proof.

Do not report installation, scheduling, or delivery as successful without observable output from the corresponding command or destination.