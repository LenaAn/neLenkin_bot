import logging
import os
import requests
from dotenv import set_key, load_dotenv

logger = logging.getLogger("patreon_token_refresher")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # prints to stdout (captured by cron log)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Should be executed via cron in < 30 days.
# At the moment of writing, Patreon access tokens live for
# one month.
def refresh_access_token() -> None:
    load_dotenv()

    client_id = os.getenv("PATREON_CLIENT_ID")
    client_secret = os.getenv("PATREON_CLIENT_SECRET")
    refresh_token = os.getenv("PATREON_REFRESH_TOKEN")

    response = requests.post(
        "https://www.patreon.com/api/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()

    tokens = response.json()

    new_access_token = tokens["access_token"]
    new_refresh_token = tokens["refresh_token"]

    set_key(".env", "PATREON_ACCESS_TOKEN", new_access_token)
    set_key(".env", "PATREON_REFRESH_TOKEN", new_refresh_token)
    logger.info("Successfully updated Patreon access token")


if __name__ == "__main__":
    refresh_access_token()
