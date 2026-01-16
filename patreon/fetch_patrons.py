import logging
import os
import requests
import redis
from typing import Optional

from dotenv import load_dotenv

from telegram import Bot

import settings

patreon_logger = logging.getLogger(__name__)
patreon_logger.setLevel(logging.DEBUG)

r = redis.Redis(host='localhost', port=6379, db=0)


async def fetch_patrons(bot: Bot) -> Optional[list[dict]]:
    load_dotenv(override=True)

    # todo: this token expires about once a month. Need to refresh it automatically
    access_token = os.getenv("PATREON_ACCESS_TOKEN")
    campaign_id = os.getenv("PATREON_CAMPAIGN_ID")
    api_url = f"https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/members"
    params = {"fields[member]": "full_name,email,patron_status,currently_entitled_amount_cents"}
    headers = {"Authorization": f"Bearer {access_token}"}
    url = api_url.format(campaign_id=campaign_id)

    all_members = []
    while url:
        try:
            patreon_logger.debug("new while url iteration")
            r = requests.get(url, headers=headers, params=params if url == api_url else None)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError as e:
            patreon_logger.warning(f"Couldn't get info from Patreon: {e}")
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Couldn't get info from Patreon: {e}",
                parse_mode="HTML")
            return None
        except Exception as e:
            patreon_logger.error(f"Unexpected error while getting info from Patreon: {e}")
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Unexpected error while getting info from Patreon: {e}",
                parse_mode="HTML")
            return None

        for m in data["data"]:
            attrs = m["attributes"]
            all_members.append(attrs)

        url = data.get("links", {}).get("next")  # go to next page if exists

    patreon_logger.info(f"Got {len(all_members)} patrons from Patreon")
    return all_members


def clear_users_from_cache() -> None:
    count = 0
    for key in r.scan_iter("user:*"):
        r.delete(key)
        count += 1
    patreon_logger.info(f"Deleted {count} user entries from Redis.")


def store_to_cache(all_patrons: [dict]) -> None:
    success_insert_count = 0
    fail_insert_count = 0

    for patron in all_patrons:
        try:
            r.hset(f"user:{str(patron['email']).lower()}",
                   mapping={
                       "full_name": str(patron['full_name']),
                       "patron_status": str(patron['patron_status']),
                       "currently_entitled_amount_cents": str(patron['currently_entitled_amount_cents'])
                   })
            success_insert_count += 1
        except Exception as e:
            fail_insert_count += 1
            patreon_logger.warning(f"Couldn't add patron to Redis: {e}")
    patreon_logger.info(f"Inserted {success_insert_count} patrons to Redis, failed to insert {fail_insert_count} patrons")


def get_user_counts_by_status(status_filter: str = "active_patron") -> (int, int):
    all_users_count = 0
    active_users_count = 0

    for key in r.scan_iter("user:*"):
        all_users_count += 1
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}

        if user_data.get("patron_status") == status_filter:
            active_users_count += 1

    patreon_logger.info(f"Found {all_users_count} in Redis, {active_users_count} of them are active")
    return all_users_count, active_users_count


def get_patrons(status_filter: str = "active_patron") -> list[(str, str)]:
    active_patrons = []

    for key in r.scan_iter("user:*"):
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}

        if user_data.get("patron_status") == status_filter:
            patreon_logger.info(f"active patron is {user_data}")
            active_patrons.append((user_data.get("full_name"), user_data.get("currently_entitled_amount_cents")))

    return active_patrons


async def load_patrons(bot: Bot):
    patrons = await fetch_patrons(bot)
    if patrons:
        # patrons may change email address, in this case old email should be deleted from cache
        clear_users_from_cache()
        store_to_cache(patrons)


def get_patron_by_email(email_to_find: str) -> Optional[dict]:
    key = f"user:{email_to_find}"

    if r.exists(key):
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}
        return user_data
    return None
