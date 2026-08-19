import logging
import subprocess
from _datetime import datetime
from zoneinfo import ZoneInfo


def get_today_date_str() -> tuple[str, str]:
    months = [
        "ЯНВАРЯ", "ФЕВРАЛЯ", "МАРТА", "АПРЕЛЯ", "МАЯ", "ИЮНЯ",
        "ИЮЛЯ", "АВГУСТА", "СЕНТЯБРЯ", "ОКТЯБРЯ", "НОЯБРЯ", "ДЕКАБРЯ"
    ]

    berlin_tz = ZoneInfo("Europe/Berlin")
    date = datetime.now(berlin_tz)

    return f"{date.day} {months[date.month - 1]}", f"{date.year} года"


async def create_certificates(name: str, tag: str) -> str:
    logging.info(f"Generating thank you certificate for {name} {tag}")

    date_str, year_str = get_today_date_str()

    with open(f"/tmp/latex/thank_you_{tag}.tex", "w", encoding="utf-8") as f:
        f.write(
            rf"\newcommand{{\Recipient}}{{{name} @{tag}}}" "\n"
            rf"\newcommand{{\DateDay}}{{{date_str}}}" "\n"
            rf"\newcommand{{\DateYear}}{{{year_str}}}" "\n"
            r"\input{./thank_you.tex}"
        )

    subprocess.run(["docker", "exec", "latex", "latexmk", "-pdf",
                    "-output-directory=/tmp/latex", f"-jobname=thank_you_{tag}", f"/tmp/latex/thank_you_{tag}.tex"],
                   check=True)
    return f"thank_you_{tag}.pdf"
