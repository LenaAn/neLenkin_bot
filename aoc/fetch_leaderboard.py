import logging
from datetime import datetime
from typing import Optional

import requests

import settings

aoc_logger = logging.getLogger(__name__)
aoc_logger.setLevel(logging.DEBUG)


def pluralize_points(n: int) -> str:
    if 11 <= n % 100 <= 19:
        return "очков"
    elif n % 10 == 1:
        return "очко"
    elif 2 <= n % 10 <= 4:
        return "очка"
    else:
        return "очков"


def fetch_leaderboard() -> Optional[dict]:
    """Fetch the private leaderboard JSON from Advent of Code."""
    year = datetime.now().year
    leaderboard_id = settings.AOC_LEADERBOARD_ID
    url = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"

    cookies = {"session": settings.AOC_SESSION_COOKIE}
    headers = {"User-Agent": "github.com/LenaAn/neLenkin_bot by @lenka_colenka"}

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        aoc_logger.warning(f"Couldn't get AoC leaderboard: {e}")
        return None
    except Exception as e:
        aoc_logger.error(f"Unexpected error fetching AoC leaderboard: {e}")
        return None


def format_leaderboard(data: dict) -> str:
    """Format the leaderboard data into a readable HTML message."""
    if not data or "members" not in data:
        return "Не удалось загрузить таблицу лидеров AoC 😢"

    members = data["members"].values()

    # Sort by stars (descending), then by last_star_ts (ascending)
    sorted_members = sorted(members, key=lambda m: (-m.get("stars", 0), m.get("last_star_ts", 0)))

    # Filter out members with 0 stars
    active_members = [m for m in sorted_members if m.get("stars", 0) > 0]

    if not active_members:
        return "Пока никто не решил ни одной задачи! 🎄"

    lines = ["<b>🎄 Advent of Code — Таблица лидеров</b>\n"]

    for i, member in enumerate(active_members, 1):
        name = member.get("name") or f"Аноним #{member.get('id', '?')}"
        stars = member.get("stars", 0)
        score = member.get("local_score", 0)

        # Medal emoji for top 3
        if i == 1:
            medal = " 🥇"
        elif i == 2:
            medal = " 🥈"
        elif i == 3:
            medal = " 🥉"
        else:
            medal = ""

        lines.append(f"{i}. <b>{name}</b> — ⭐{stars} ({score} {pluralize_points(score)}){medal}")

    return "\n".join(lines)


def get_formatted_leaderboard() -> str:
    """Fetch and format the leaderboard in one call."""
    data = fetch_leaderboard()
    return format_leaderboard(data)
