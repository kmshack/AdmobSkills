# AdMob Skills

[한국어](README.ko.md)

A portable [Agent Skill](https://agentskills.io/specification) for connecting to Google AdMob from Codex, Claude Code, and compatible agents.

| Use case | Included |
| --- | --- |
| **Reporting API** | Google OAuth setup, publisher account lookup, app and ad-unit inventory, and AdMob Network or Mediation reports. Includes a Python 3.9+ CLI. |
| **Mobile SDK** | Native Android and iOS integration guidance for SDK setup, UMP consent, test ads, and troubleshooting. Covers both Android GMA Next-Gen and Legacy projects. |

## Install the skill

Clone the repository, then copy the entire `skills/google-admob/` folder to the skill directory for your client. Copy it from the clone into your **target project** if you want project-level installation.

```sh
git clone https://github.com/kmshack/AdmobSkills.git
```

| Client | Project directory | Personal directory | Invoke |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | `~/.agents/skills/` | `$google-admob` or select it from `/skills` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | `/google-admob` |

For example, from the directory containing the clone, install for your user on macOS or Linux.

```sh
# Codex
mkdir -p "$HOME/.agents/skills"
cp -R AdmobSkills/skills/google-admob "$HOME/.agents/skills/"

# Claude Code
mkdir -p "$HOME/.claude/skills"
cp -R AdmobSkills/skills/google-admob "$HOME/.claude/skills/"
```

Open a session in the project you want to work on. For another Agent Skills client, copy the same folder into its documented skill directory. Report execution needs a shell, Python 3.9+, outbound HTTPS access to Google, and credentials available to that process. [Codex skill setup](https://learn.chatgpt.com/docs/build-skills), [Claude Code skill setup](https://code.claude.com/docs/en/skills)

## Try it

Prefix either prompt with `$google-admob` in Codex or `/google-admob` in Claude Code.

- “Fetch yesterday’s estimated AdMob Network earnings and impressions by app. Use my publisher’s reporting time zone and flag missing data.”
- “Add an anchored adaptive test banner to this Android screen. Reuse the project’s Google Mobile Ads SDK and UMP consent flow.”

## Run a report from your terminal

1. Follow the [local OAuth setup](skills/google-admob/references/oauth-setup.md), or supply an existing `ADMOB_ACCESS_TOKEN` or the three refresh variables from the [reporting API reference](skills/google-admob/references/reporting-api.md).
2. From the cloned repository root, check the account and run a report. Replace the example publisher ID and dates with your values. Both dates are included.

```sh
ADMOB_CLI=skills/google-admob/scripts/admob.py
python3 "$ADMOB_CLI" accounts

PUB_ID=pub-1234567890123456
python3 "$ADMOB_CLI" report --publisher-id "$PUB_ID" \
  --type network --start-date 2026-01-01 --end-date 2026-01-07 \
  --dimension DATE --dimension APP \
  --metric IMPRESSIONS --metric ESTIMATED_EARNINGS
```

Use `--type mediation` when the report should cover mediated sources. Run `python3 "$ADMOB_CLI" --help` for account, inventory, and report commands. App and ad-unit inventory requires the `admob.readonly` scope. Inspect the JSON report header for currency and time zone, and the footer for data warnings or row limits. Keep OAuth credentials and raw account data outside the repository.

## Project layout

- [Skill entry point](skills/google-admob/SKILL.md)
- [OAuth setup](skills/google-admob/references/oauth-setup.md) and [Reporting API](skills/google-admob/references/reporting-api.md)
- [Native mobile SDK guide](skills/google-admob/references/mobile-sdk.md)
- [Reporting CLI](skills/google-admob/scripts/admob.py)

## License

[MIT](LICENSE)
