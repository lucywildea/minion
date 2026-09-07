# Minion agent entry point

For any request to install, configure, run, automate, update, or troubleshoot Minion, read and follow [`integrations/hermes/skills/minion/SKILL.md`](integrations/hermes/skills/minion/SKILL.md) before acting.

If the agent is Hermes, complete the integration as one setup after obtaining approval for installation, configuration, and restart actions:

1. Install or update the Minion release binary for the detected operating system and architecture by following [`integrations/hermes/skills/minion/references/setup.md`](integrations/hermes/skills/minion/references/setup.md).
2. Verify `minion --version` and `minion --help`.
3. Install the normal user skill:
   `hermes skills install https://raw.githubusercontent.com/lugenx/minion/main/integrations/hermes/skills/minion/SKILL.md --name minion`
4. Install and enable the web provider:
   `hermes plugins install lugenx/minion/integrations/hermes --enable`
5. Select it for search:
   `hermes config set web.search_backend minion`
6. Restart Hermes, start a new session, and verify one real `web_search` call.

The Hermes plugin is an adapter to the Minion binary already installed on the operating system. It must not install, bundle, or maintain another Minion copy.

For other agents, install the repository skill using the environment's normal skill mechanism when available. Otherwise, follow the skill directly from this repository.

Use the current repository code and live `minion ... --help` output as the source of truth.