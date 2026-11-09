# AdMob reporting API reference

## Authentication and account selection

Enable the AdMob API in a Google Cloud project and authorize with a Google user who has access to the target AdMob account. For report-only access, use `https://www.googleapis.com/auth/admob.report`. Use `https://www.googleapis.com/auth/admob.readonly` when the workflow needs app or ad-unit inventory. The OAuth scope and the user's AdMob role both affect access. [AdMob API setup](https://developers.google.com/admob/api/v1/getting-started)

The bundled Python CLI checks for credentials in this order.

1. An existing `ADMOB_ACCESS_TOKEN`.
2. The complete `ADMOB_CLIENT_ID`, `ADMOB_CLIENT_SECRET`, and `ADMOB_REFRESH_TOKEN` environment variable set.
3. `ADMOB_CREDENTIALS_FILE`, the path to a local authorized-user JSON file containing `client_id`, `client_secret`, and `refresh_token`.

If the process has any refresh variables set, supply all three or unset them to use the file.

The refresh credentials must belong to the same OAuth client and user grant. Keep them in a local secret store or process environment. Exclude them from commits, prompts, command arguments, and diagnostic logs. First-time consent uses Google's OAuth flow outside the CLI. Desktop clients use a system browser and a loopback redirect. External OAuth projects in Testing issue refresh tokens that expire after seven days for AdMob scopes. [Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app), [Refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration)

Run `python3 scripts/admob.py accounts` from the skill directory to look up the publisher ID, default currency, and reporting timezone. `accounts.list` is documented to return the publisher account most recently signed in to through the AdMob UI. Use `account --publisher-id` to verify a known publisher and its reporting defaults. Use the `pub-…` ID for `--publisher-id`. App IDs contain `~` and ad unit IDs contain `/`. [List publisher accounts](https://developers.google.com/admob/api/reference/rest/v1/accounts/list), [Get account](https://developers.google.com/admob/api/reference/rest/v1/accounts/get)

## REST requests

Use `https://admob.googleapis.com/v1` as the base URL with a bearer token. In the table, `{publisherId}` is the `pub-…` identifier.

| Method and path | Purpose | Accepted AdMob scope | Google reference |
| --- | --- | --- | --- |
| `GET /accounts` | Account discovery | `report` or `readonly` | [List accounts](https://developers.google.com/admob/api/reference/rest/v1/accounts/list) |
| `GET /accounts/{publisherId}` | Verify a known publisher and its defaults | `report` or `readonly` | [Get account](https://developers.google.com/admob/api/reference/rest/v1/accounts/get) |
| `GET /accounts/{publisherId}/apps` | App inventory | `readonly` | [List apps](https://developers.google.com/admob/api/reference/rest/v1/accounts.apps/list) |
| `GET /accounts/{publisherId}/adUnits` | Ad unit inventory | `readonly` | [List ad units](https://developers.google.com/admob/api/reference/rest/v1/accounts.adUnits/list) |
| `POST /accounts/{publisherId}/networkReport:generate` | AdMob Network performance | `report` or `readonly` | [Generate a network report](https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate) |
| `POST /accounts/{publisherId}/mediationReport:generate` | Mediation performance including third-party sources | `report` or `readonly` | [Generate a mediation report](https://developers.google.com/admob/api/reference/rest/v1/accounts.mediationReport/generate) |

The CLI collects each inventory list across pages. For a direct inventory request, follow `nextPageToken` as `pageToken` until the token is absent. The collection keys are `account`, `apps`, and `adUnits`. For app names and platform, use the app record. For ad-unit ownership, join `adUnits[].appId` to `apps[].appId`.

Report requests wrap the specification in `reportSpec`. `dateRange.startDate` and `dateRange.endDate` are both inclusive and use objects containing `year`, `month`, and `day`. The CLI accepts ISO dates. By omitting the `timeZone` field, it uses the account's reporting timezone. Google documents `America/Los_Angeles` as the only explicit override. Use the returned reporting timezone to interpret `DATE` buckets, and report that timezone when it differs from the user's requested timezone. Daily buckets alone are insufficient to reconstruct a day in a different timezone. [Date range](https://developers.google.com/admob/api/reference/rest/v1/DateRange), [Report spec](https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate#networkreportspec), [Report header](https://developers.google.com/admob/api/reference/rest/v1/ReportHeader)

Start with a short, completed date range and the CLI defaults (`DATE`, `IMPRESSIONS`, `ESTIMATED_EARNINGS`). For daily app results, pass `--dimension DATE --dimension APP`. For a mediation source breakdown, use `--type mediation` and include `AD_SOURCE`. Use at most one of `DATE`, `WEEK`, or `MONTH`. Google includes `APP` automatically with `AD_UNIT`. Check the selected report's enum and compatibility rules when adding fields. For example, network `AD_TYPE` conflicts with `AD_REQUESTS`, `MATCH_RATE`, and `IMPRESSION_RPM`. Network and mediation figures can overlap, so use the report type that matches the user's requested coverage. [Reporting overview](https://developers.google.com/admob/api/v1/report-overview), [Network report fields](https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate#networkreportspec), [Mediation report fields](https://developers.google.com/admob/api/reference/rest/v1/accounts.mediationReport/generate#mediationreportspec)

## Interpret and validate the response

The CLI emits JSON and preserves the report's REST array. Read its `header`, the entries containing `row`, and the final `footer`. Treat a missing header or footer as an incomplete response. Keep the reported date range, timezone, and currency with the data. `--currency` changes `localizationSettings.currencyCode`. Omitting it uses the account currency. Google uses daily average exchange rates when it converts currency. [Report header](https://developers.google.com/admob/api/reference/rest/v1/ReportHeader), [Localization settings](https://developers.google.com/admob/api/reference/rest/v1/LocalizationSettings)

- Group using `dimensionValues[dimension].value`, and display `displayLabel` when present. Stable IDs help when labels change or collide. The `DATE` dimension is returned as `YYYYMMDD`.
- Preserve count fields (`integerValue`) and money fields (`microsValue`) as exact integers when parsing. Convert monetary micros to currency units by dividing by `1,000,000`. For example, `"2400000"` represents `2.40` in the report currency. Rates use `doubleValue` and are usually formatted as percentages after multiplying by 100. [Report row types](https://developers.google.com/admob/api/reference/rest/v1/ReportRow)
- Keep missing metrics and dates distinguishable from observed zeros. Use `null` or a clear unavailable marker when a field is absent, access is restricted, or the source is delayed. Only aggregate available values when you can disclose their coverage. Identify `ESTIMATED_EARNINGS` as estimated revenue. [Report row types](https://developers.google.com/admob/api/reference/rest/v1/ReportRow), [Track earnings](https://support.google.com/admob/answer/3005530)
- Recompute grouped rates from the underlying totals. CTR uses clicks divided by impressions, match rate uses matched requests divided by ad requests, and show rate uses impressions divided by matched requests. Calculate revenue-based eCPM as earnings in currency units divided by impressions, multiplied by 1,000. Return an unavailable rate when its denominator is zero or missing. `OBSERVED_ECPM` is a separate mediation metric. [Network metrics](https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate#metric), [Mediation metrics](https://developers.google.com/admob/api/reference/rest/v1/accounts.mediationReport/generate#metric)
- In mediation, a single app request can reach several sources. Summing `AD_REQUESTS` across `AD_SOURCE` or `AD_SOURCE_INSTANCE` rows can count it more than once. For unique requests and overall request-based rates, run a separate report at the desired level without the ad source breakdown. [AdMob request counting](https://support.google.com/admob/answer/10979428)
- Check `footer.warnings` for issues such as `DATA_DELAYED`, `DATA_BEFORE_ACCOUNT_TIMEZONE_CHANGE`, or `REPORT_CURRENCY_NOT_ACCOUNT_CURRENCY`. Inspect `matchingRowCount` alongside the returned row count and the effective row cap. The matching count may differ from the number of rows in the response. If a report reaches the cap, check coverage before treating totals as complete. [Report footer](https://developers.google.com/admob/api/reference/rest/v1/ReportFooter)
- Reports cap returned rows at 100,000, and `--max-rows` can lower the cap. For a complete high-cardinality export, split into non-overlapping date ranges or reduce dimensions. Preserve the `DATE` dimension when stitching daily data, and recalculate aggregate rates after combining additive totals. Use closed periods for comparisons and label recent data as provisional when relevant. [Report limits](https://developers.google.com/admob/api/v1/report-overview#reduce-report-limits)

## Troubleshooting

| Symptom | Check |
| --- | --- |
| OAuth `invalid_grant` | Confirm the refresh token belongs to the configured client and has not expired or been revoked. If needed, have the user reauthorize through Google. |
| `401 UNAUTHENTICATED` | Refresh or replace the access token and confirm the process is using the intended credential. |
| `403 PERMISSION_DENIED` | Confirm the API is enabled for the OAuth project's client, the grant has the endpoint's scope, and the Google user has the relevant AdMob account permissions. |
| `400 INVALID_ARGUMENT` | Verify the publisher resource, date range, timezone override, and field enums for the selected report type. Retry with `DATE` and `IMPRESSIONS` to isolate a spec error. |
| `429` or a transient `5xx` | Check quota and use bounded retries with backoff for read requests. Honor `Retry-After` when supplied. If a large report hits a quota error, shorten the date range or reduce the number of dimensions. |
| Empty report or mismatch with the AdMob UI | Compare publisher, report type, filters, timezone, currency, user permissions, and date range. Inspect the footer and report the gap separately from any returned zeros. |

[AdMob authorization](https://developers.google.com/admob/api/v1/how-tos/authorizing), [OAuth error handling](https://developers.google.com/identity/protocols/oauth2/native-app), [Common AdMob API errors](https://developers.google.com/admob/api/v1/errors), [AdMob API quotas](https://developers.google.com/admob/api/quotas)
