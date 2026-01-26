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
            r.hset(f"boosty:user:{str(boosty_patron['email']).lower()}",
                   mapping={
                       "name": str(boosty_patron['name']),
                       "price": str(boosty_patron['price']),
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
