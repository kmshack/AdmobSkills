# Authorize AdMob reporting locally

Use this setup once for a new OAuth grant. An existing authorized integration can supply a short-lived `ADMOB_ACCESS_TOKEN` or the refresh variables described in [AdMob reporting API](reporting-api.md).

## 1. Set up the Google Cloud project

1. Select or create a Google Cloud project and enable the **AdMob API** in its API Library.
2. Configure the OAuth consent screen in Google Auth Platform. If your audience is External and the app is in Testing, add the Google account that will authorize the request as a test user. That account also needs access to the intended AdMob publisher.
3. Create an OAuth client of type **Desktop app**. Create the private directory below, then save the downloaded client JSON as `~/.config/admob-skills/client-secret.json`.

```sh
umask 077
mkdir -p "$HOME/.config/admob-skills"
chmod 700 "$HOME/.config/admob-skills"
```

[Google AdMob API setup](https://developers.google.com/admob/api/v1/getting-started), [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)

## 2. Authorize in your browser

Run the commands in a local macOS or Linux shell with Python and a browser. The OAuth helper uses Google's Python library and a loopback redirect. The reporting CLI itself uses only the Python standard library.

```sh
umask 077
chmod 600 "$HOME/.config/admob-skills/client-secret.json"

export ADMOB_OAUTH_CLIENT_FILE="$HOME/.config/admob-skills/client-secret.json"
export ADMOB_CREDENTIALS_FILE="$HOME/.config/admob-skills/authorized-user.json"
export ADMOB_SCOPE="https://www.googleapis.com/auth/admob.report"
# Use https://www.googleapis.com/auth/admob.readonly for app and ad-unit inventory.

python3 -m venv "$HOME/.config/admob-skills/oauth-venv"
"$HOME/.config/admob-skills/oauth-venv/bin/python" -m pip install google-auth-oauthlib
```

```sh
"$HOME/.config/admob-skills/oauth-venv/bin/python" - <<'PY'
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

output = Path(os.environ["ADMOB_CREDENTIALS_FILE"]).expanduser()
if output.exists():
    raise SystemExit("Credential file already exists. Choose a new private path to reauthorize.")

flow = InstalledAppFlow.from_client_secrets_file(
    os.environ["ADMOB_OAUTH_CLIENT_FILE"],
    scopes=[os.environ["ADMOB_SCOPE"]],
    autogenerate_code_verifier=True,
)
credentials = flow.run_local_server(host="127.0.0.1", port=0, prompt="consent")
if not credentials.refresh_token:
    raise SystemExit("Google returned no refresh token. Check the consent flow and reauthorize.")

with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
    json.dump(
        {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "refresh_token": credentials.refresh_token,
        },
        file,
    )
print("Saved local AdMob credentials.")
PY
```

In the browser, select the Google account with access to the intended publisher and review the requested scope before granting access. Treat both the downloaded JSON and the generated credential file as secrets. [Google OAuth library](https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html)

## 3. Confirm account access

Run the following from the cloned `skills/google-admob/` or installed `google-admob/` directory. In later shells, set `ADMOB_CREDENTIALS_FILE` to the same path or provide it through your secret manager.

```sh
export ADMOB_CREDENTIALS_FILE="$HOME/.config/admob-skills/authorized-user.json"
python3 scripts/admob.py accounts
```

Check the returned `publisherId`, `reportingTimeZone`, and `currencyCode`. If you already know the intended ID, verify it with `python3 scripts/admob.py account --publisher-id pub-1234567890123456`, using your own publisher ID.

If the CLI uses an unexpected identity or scope, check for an existing `ADMOB_ACCESS_TOKEN` or refresh variables that take precedence. A scope change needs a new grant. For an External OAuth app in Testing, refresh tokens issued with AdMob scopes expire after seven days. If Google revokes the grant or the token expires, authorize again and update the credential path in the process running the CLI. [Google token expiration rules](https://developers.google.com/identity/protocols/oauth2#expiration)
