#!/usr/bin/env python3
"""Read inventory and generate reports with the Google AdMob v1 REST API."""

import argparse
import http.client
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_URL = "https://admob.googleapis.com/v1"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TIMEOUT_SECONDS = 120
MAX_REPORT_ROWS = 100_000
REFRESH_ENV = {
    "client_id": "ADMOB_CLIENT_ID",
    "client_secret": "ADMOB_CLIENT_SECRET",
    "refresh_token": "ADMOB_REFRESH_TOKEN",
}


class AdMobError(Exception):
    """An error whose message can be displayed without exposing credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(NoRedirect)


def request_json(url, *, token=None, payload=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    operation = "AdMob API"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    if form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urlencode(form).encode("ascii")
        operation = "Google OAuth token refresh"

    try:
        with OPENER.open(Request(url, data=body, headers=headers), timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as error:
        error.close()
        hints = {
            400: "Check the requested fields, date range, and report type.",
            401: "Check whether the access token is expired or revoked.",
            403: "Check the OAuth scope, API enablement, and AdMob account access.",
            404: "Check the publisher ID and your access to the account.",
            429: "Check quota and retry with backoff.",
        }
        hint = hints.get(error.code, "")
        if form is not None and error.code in (400, 401):
            hint = "Check the client credentials and whether the refresh token is valid for this client."
        if 500 <= error.code < 600:
            hint = "Google returned a server error. Retry with backoff."
        raise AdMobError(f"{operation} returned HTTP {error.code}. {hint}".rstrip()) from None
    except (OSError, http.client.HTTPException):
        raise AdMobError(f"{operation} could not complete the HTTPS request.") from None
    except ValueError:
        raise AdMobError(f"{operation} returned invalid JSON.") from None


def load_refresh_credentials():
    credentials = {field: os.environ.get(var) for field, var in REFRESH_ENV.items()}
    if any(credentials.values()):
        if not all(credentials.values()):
            raise AdMobError("Set ADMOB_CLIENT_ID, ADMOB_CLIENT_SECRET, and ADMOB_REFRESH_TOKEN together.")
        return credentials

    credential_file = os.environ.get("ADMOB_CREDENTIALS_FILE")
    if not credential_file:
        raise AdMobError(
            "Configure ADMOB_ACCESS_TOKEN, the three OAuth refresh variables, "
            "or ADMOB_CREDENTIALS_FILE before querying AdMob."
        )
    try:
        data = json.loads(Path(credential_file).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError, RuntimeError):
        raise AdMobError("Could not read a valid JSON file from ADMOB_CREDENTIALS_FILE.") from None
    if not isinstance(data, dict) or any(
        not isinstance(data.get(field), str) or not data[field].strip() for field in REFRESH_ENV
    ):
        raise AdMobError("The credential file needs client_id, client_secret, and refresh_token.")
    return {field: data[field] for field in REFRESH_ENV}


def access_token():
    token = os.environ.get("ADMOB_ACCESS_TOKEN")
    if not token:
        form = {"grant_type": "refresh_token", **load_refresh_credentials()}
        response = request_json(TOKEN_URL, form=form)
        token = response.get("access_token") if isinstance(response, dict) else None
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", token):
        raise AdMobError("The access token is missing or has an invalid format.")
    return token


def list_resources(path, field, token):
    items = []
    seen_tokens = set()
    url = f"{API_URL}/{path}"
    while True:
        response = request_json(url, token=token)
        if not isinstance(response, dict):
            raise AdMobError("AdMob returned an unexpected inventory response.")
        page = response.get(field, [])
        next_token = response.get("nextPageToken", "")
        if not isinstance(page, list) or not isinstance(next_token, str):
            raise AdMobError("AdMob returned an unexpected inventory response.")
        items.extend(page)
        if not next_token:
            return {field: items}
        if next_token in seen_tokens:
            raise AdMobError("AdMob repeated a page token. Inventory could not be collected.")
        seen_tokens.add(next_token)
        url = f"{API_URL}/{path}?{urlencode({'pageToken': next_token})}"


def date_parts(value):
    return {"year": value.year, "month": value.month, "day": value.day}


def generate_report(args, token):
    spec = {
        "dateRange": {"startDate": date_parts(args.start_date), "endDate": date_parts(args.end_date)},
        "dimensions": args.dimension or ["DATE"],
        "metrics": args.metric or ["IMPRESSIONS", "ESTIMATED_EARNINGS"],
    }
    if args.currency:
        spec["localizationSettings"] = {"currencyCode": args.currency}
    if args.max_rows:
        spec["maxReportRows"] = args.max_rows

    path = f"accounts/{args.publisher_id}/{args.type}Report:generate"
    report = request_json(f"{API_URL}/{path}", token=token, payload={"reportSpec": spec})
    if (
        not isinstance(report, list)
        or len(report) < 2
        or not all(isinstance(message, dict) for message in report)
        or not isinstance(report[0].get("header"), dict)
        or not isinstance(report[-1].get("footer"), dict)
        or any(not isinstance(message.get("row"), dict) for message in report[1:-1])
    ):
        raise AdMobError("AdMob returned an incomplete or unexpected report. Check the request before retrying.")

    if report[-1]["footer"].get("warnings"):
        print("AdMob returned report warnings. Inspect footer.warnings.", file=sys.stderr)
    if len(report) - 2 >= (args.max_rows or MAX_REPORT_ROWS):
        print("The report reached its row limit. Check the footer before using totals.", file=sys.stderr)
    return report


def iso_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return parsed
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("expected a calendar date in YYYY-MM-DD format")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("accounts", help="list the publisher account returned by AdMob")

    for command, help_text in (
        ("account", "get a specific publisher account"),
        ("apps", "list apps"),
        ("ad-units", "list ad units"),
        ("report", "generate a report"),
    ):
        sub = commands.add_parser(command, help=help_text)
        sub.add_argument("--publisher-id", required=True, help="AdMob publisher ID such as pub-1234567890123456")

    report = commands.choices["report"]
    report.add_argument("--type", choices=("network", "mediation"), default="network", help="report type (default: network)")
    report.add_argument("--start-date", type=iso_date, required=True, help="first included date in YYYY-MM-DD format")
    report.add_argument("--end-date", type=iso_date, required=True, help="last included date in YYYY-MM-DD format")
    report.add_argument("--dimension", action="append", help="repeat for each dimension (default: DATE)")
    report.add_argument("--metric", action="append", help="repeat for each metric (default: IMPRESSIONS and ESTIMATED_EARNINGS)")
    report.add_argument("--currency", help="three-letter currency code (default: account currency)")
    report.add_argument("--max-rows", type=int, help="row limit from 1 through 100000")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    publisher_id = getattr(args, "publisher_id", None)
    if publisher_id is not None and not re.fullmatch(r"pub-[0-9]+", publisher_id):
        parser.error("--publisher-id must have the form pub- followed by digits")
    if args.command == "report":
        if args.start_date > args.end_date:
            parser.error("--start-date must be on or before --end-date")
        if args.currency is not None and not re.fullmatch(r"[A-Z]{3}", args.currency):
            parser.error("--currency must be a three-letter uppercase currency code")
        if args.max_rows is not None and not 1 <= args.max_rows <= MAX_REPORT_ROWS:
            parser.error("--max-rows must be between 1 and 100000")

    try:
        token = access_token()
        if args.command == "accounts":
            result = list_resources("accounts", "account", token)
        elif args.command == "account":
            result = request_json(f"{API_URL}/accounts/{publisher_id}", token=token)
        elif args.command == "apps":
            result = list_resources(f"accounts/{publisher_id}/apps", "apps", token)
        elif args.command == "ad-units":
            result = list_resources(f"accounts/{publisher_id}/adUnits", "adUnits", token)
        else:
            result = generate_report(args, token)

        json.dump(result, sys.stdout, indent=2)
        print()
        return 0
    except AdMobError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
