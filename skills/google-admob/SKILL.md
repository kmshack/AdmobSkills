---
name: google-admob
description: Connect to Google AdMob for OAuth, account and inventory lookup, and network or mediation reports. Integrate or troubleshoot Google Mobile Ads and UMP in native Android and iOS apps.
---

# Google AdMob

- For OAuth, publisher accounts, app or ad unit inventory, and earnings reports, read [AdMob Reporting API](references/reporting-api.md).
- For a first-time OAuth grant, direct the user to [Local OAuth setup](references/oauth-setup.md).
- For adding or debugging ads in a native Android or iOS project, read [Mobile SDK integration](references/mobile-sdk.md).
- If the user asks for both, keep reporting credentials outside the app and verify each route separately.

## Reporting workflow

1. Identify the publisher account, report type, requested dates, and breakdown. Use a network report for AdMob Network and a mediation report for coverage that includes mediated sources. Use the account reporting time zone for relative dates such as “yesterday” unless the user specifies a time zone. If the requested day boundaries differ from the available daily buckets, disclose that difference. Check the account and report header for the effective time zone and currency, and state the resolved dates.
2. Use an existing authorized integration when available. Otherwise, run [admob.py](scripts/admob.py) with Python 3.9 or newer from the skill directory, or call it by absolute path. Run `python3 scripts/admob.py --help` for commands. Use `admob.report` for account and report queries, or `admob.readonly` when app or ad unit inventory is also needed. If authorization is missing, direct the user to complete Google consent locally and supply credentials through their environment or a private credential file.
3. Check the report footer, the observed row count, and coverage for the requested dates and breakdown. Preserve currency and original units until conversion. Keep empty data, partial data, failed queries, and observed zeros distinct. Report the source, scope, dates, currency, and material limitations with the results.
4. Keep OAuth tokens and credential values out of source files, command arguments, logs, and responses. Keep raw reports and inventory in the user's private workspace unless sharing is requested. Report Google errors without repeating sensitive account data.

## Mobile integration workflow

1. Inspect the existing SDK variant, build configuration, app IDs, ad wrappers, and consent flow. Match the current platform and SDK documentation to the project.
2. Connect the requested placement through the existing app entry points. Use platform-specific test ad IDs or configured test devices for verification. Check consent, initialization, loading, cleanup, and failure handling.
3. State which builds and device scenarios were verified, along with any remaining prerequisites for live ad delivery.
