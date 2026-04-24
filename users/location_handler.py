import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import Update
from telegram.ext import ContextTypes

import helpers
import models
import settings


def current_locations_summary(list_of_locations: list[models.Location]) -> str:
    if len(list_of_locations) == 0:
        curr_locations_summary = 'Ты не подписан на новости о сходках ни в какой локации.'
    else:
        curr_locations_summary = "Ты подписан на новости о сходках в\n - "
        curr_locations_summary += "\n - ".join(list_of_locations)
        curr_locations_summary += "\n\nЕсли хочешь отписаться от новостей для какой-то локации, напиши @lenka_colenka."
    return curr_locations_summary


def get_current_locations(tg_id: str) -> list[str]:
    with Session(models.engine) as session:
        stmt = (
            select(models.Location)
            .join(models.UserLocation, models.Location.id == models.UserLocation.location_id)
            .where(models.UserLocation.tg_id == tg_id)
        )
        result = session.execute(stmt).scalars().all()
        locations = list(result)
    logging.info(f"{locations=}")
    return [f"{location.city_name.capitalize()}, {location.country_name.capitalize()}" for location in locations]


async def add_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"add_location_handler triggered by {helpers.repr_user_from_update(update)}")
    tg_id = str(update.effective_user.id)

    args = context.args
    if len(args) != 2:
        instruction: str = ("Введи город и страну по-русски, как они написаны на Википедии. Пример:"
                            "\n\n/add_location Белград Сербия"
                            "\n\nЕсли хочешь получать новости о сходках в нескольких городах, добавь каждый город "
                            "отдельной командой.")
        list_of_locations = get_current_locations(tg_id)
        current_locations_reply = current_locations_summary(list_of_locations)
        await update.effective_message.reply_text(f"{instruction}\n\n{current_locations_reply}")
        return

    city = args[0].lower()
    country = args[1].lower()
    # try to insert current location as new
    # if we fail with Unique constraint violation, it's expected, just get the location id
    with Session(models.engine) as session:
        stmt = select(models.Location).where(
            models.Location.city_name == city,
            models.Location.country_name == country
        )
        location = session.scalar(stmt)

        if not location:
            location = models.Location(city_name=city, country_name=country)
            session.add(location)
            session.flush()

        user_location = models.UserLocation(
            tg_id=tg_id,
            location_id=location.id
        )
        session.add(user_location)

        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add location {city} {country} for {helpers.repr_user_from_update(update)} to db: {e}")

    logging.info(f"New location for {helpers.repr_user_from_update(update)}: {city.capitalize()}, {country.capitalize()}")
    await context.bot.send_message(
        chat_id=settings.ADMIN_CHAT_ID,
        text=f"New location for {helpers.repr_user_from_update(update)}: {city.capitalize()}, {country.capitalize()}"
    )

    list_of_locations = get_current_locations(str(update.effective_user.id))
    current_locations_reply = current_locations_summary(list_of_locations)
    await update.effective_message.reply_text(current_locations_reply)
