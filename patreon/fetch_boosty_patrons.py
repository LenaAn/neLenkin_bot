import logging
from typing import Optional

import redis
from telegram import Bot
from boosty_api import BoostyAPI

import settings

boosty_logger = logging.getLogger(__name__)
boosty_logger.setLevel(logging.DEBUG)

r = redis.Redis(host='localhost', port=6379, db=0)

boosty_api: Optional[BoostyAPI] = None
blog_href: Optional[str] = None


async def init():
    global boosty_api, blog_href
    boosty_api = await BoostyAPI.create("auth.json")
    blog_href = await boosty_api.get_blog_href()


async def close():
    if boosty_api:
        boosty_logger.info("Closing Boosty API...")
        await boosty_api.close()


async def fetch_boosty_patrons(bot: Bot) -> Optional[list[dict]]:
    boosty_all_members = []

    try:
        stats = await boosty_api.get_subscribers()

        if stats["total"] != len(stats["data"]):
            boosty_logger.warning(f"Couldn't get all subscribers from Boosty, need pagination! Total is "
                                  f"{stats['total']}, got {len(stats['data'])} subscribers.")
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Couldn't get all subscribers from Boosty, need pagination! Total is {stats['total']}, got "
                     f"{len(stats['data'])} subscribers.",
                parse_mode="HTML")
            return None

        for subscriber in stats["data"]:
            boosty_all_members.append({
                "id": subscriber["id"],
                "email": subscriber["email"],
                "name": subscriber["name"],
                "price": subscriber["price"],
            })
        return boosty_all_members
    except Exception as e:
        boosty_logger.error(f"Unexpected error while getting info from Boosty: {e}")
        await bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"Unexpected error while getting info from Boosty: {e}",
            parse_mode="HTML")
        return None


def clear_boosty_patrons_from_cache() -> None:
    count = 0
    for key in r.scan_iter("boosty:user:*"):
        r.delete(key)
        count += 1
    boosty_logger.info(f"Deleted {count} Boosty user entries from Redis.")


def store_boosty_patrons_to_cache(all_boosty_patrons: [dict]) -> None:
    success_insert_count = 0
    fail_insert_count = 0

    for boosty_patron in all_boosty_patrons:
        try:
            r.hset(f"boosty:user:{boosty_patron['id']}",
                   mapping={
                       "email": boosty_patron['email'],
                       "name": boosty_patron['name'],
                       "price": boosty_patron['price'],
                   })
            success_insert_count += 1
        except Exception as e:
            fail_insert_count += 1
            boosty_logger.warning(f"Couldn't add Boosty patron to Redis: {e}")
    boosty_logger.info(f"Inserted {success_insert_count} Boosty patrons to Redis, failed to insert {fail_insert_count} "
                       f"Boosty patrons")


async def load_boosty_patrons(bot: Bot):
    boosty_patrons = await fetch_boosty_patrons(bot)
    if boosty_patrons:
        # boosty patrons may change email address, in this case old email should be deleted from cache
        clear_boosty_patrons_from_cache()
        store_boosty_patrons_to_cache(boosty_patrons)


def get_boosty_patrons_from_redis(min_price_rub: int) -> list[(str, str)]:
    active_boosty_patrons = []

    for key in r.scan_iter("boosty:user:*"):
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}

        if int(user_data.get("price")) > 0:
            boosty_logger.info(f"paid boosty subscriber is {user_data}")
            boosty_patron_info = [user_data.get("name"), user_data.get("email"), user_data.get("price")]
            active_boosty_patrons.append(boosty_patron_info)

    return active_boosty_patrons


def get_boosty_info(boosty_user_id: str) -> Optional[dict]:
    # todo: maybe need to reload from Boosty somewhere here
    key = f"boosty:user:{boosty_user_id}"

    if r.exists(key):
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}
        return user_data
    return None


# user_input should be either email or name
# slower method than `get_boosty_info`, use only when boosty_user_id is not present
# works in O(n) where n is a number of Boosty users
def get_boosty_info_by_field(user_input: str = None) -> Optional[tuple[str, dict]]:
    user_input = user_input.lower()
    for key in r.scan_iter("boosty:user:*"):
        user_data = r.hgetall(key)
        user_data = {k.decode(): v.decode() for k, v in user_data.items()}

        if user_data.get("email").lower() == user_input or user_data.get("name").lower() == user_input:
            return key.decode().split(':')[2], user_data
    return None
