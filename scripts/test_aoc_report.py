# /// script
# dependencies = ["dotenv", "requests"]
# ///
"""
Make sure .env has AOC_SESSION_COOKIE and AOC_LEADERBOARD_ID set.

Get session cookie:

  1. Go to https://adventofcode.com and log in
  2. Open browser DevTools (F12 typically)
  3a. When using Firefox, go to Storage tab and expand Cookies to get the one for https://adventofcode.com
  3b. When using Chrome, the tab is called Application
  4. Find the cookie named `session` and copy its Value
  5. Paste it into your .env:
  AOC_SESSION_COOKIE=53616c7465645f5f...

uv run scripts/test_aoc_report.py

"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from aoc import fetch_leaderboard


def main():
    print("Fetching AoC leaderboard...\n")

    data = fetch_leaderboard.fetch_leaderboard()

    if data is None:
        print("ERROR: Failed to fetch leaderboard. Check your AOC_SESSION_COOKIE and AOC_LEADERBOARD_ID.")
        sys.exit(1)

    print(f"Raw data has {len(data.get('members', {}))} members\n")
    print("=" * 50)
    print("Formatted report (HTML tags visible):")
    print("=" * 50)
    print(fetch_leaderboard.format_leaderboard(data))
    print("=" * 50)


if __name__ == "__main__":
    main()
