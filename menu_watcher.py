import os
import re
import sys
import smtplib
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from unidecode import unidecode


def log(msg: str) -> None:
    print(msg, flush=True)


def within_send_window(now: datetime) -> bool:
    # Monday is 0, Sunday is 6
    return now.weekday() < 5 and now.hour == 7


def fetch_menu(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "").lower()
    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        log("parse pdf")
        return extract_text(BytesIO(resp.content))
    log("parse html")
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    text = soup.get_text(separator=" ")
    return text


def normalise(text: str) -> str:
    return unidecode(text.lower())


def find_matches(text: str, keywords, regex):
    text_lower = text.lower()
    norm = normalise(text)
    found = set()
    for kw in keywords:
        kw_l = kw.lower()
        if kw_l in text_lower or normalise(kw_l) in norm:
            found.add(kw)
    if regex:
        pattern = re.compile(regex, re.IGNORECASE)
        if pattern.search(text) or pattern.search(norm):
            found.add(f"regex:{regex}")
    return found


def send_email(matches, snippet, url, now):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "0"))
    user = os.getenv("SMTP_USERNAME")
    pw = os.getenv("SMTP_PASSWORD")
    to = os.getenv("SMTP_TO")
    mail_from = os.getenv("SMTP_FROM") or user
    if not all([host, port, user, pw, to]):
        log("missing smtp configuration; skip sending")
        return
    msg = EmailMessage()
    msg["Subject"] = f"[Macchi-Älplermagronen-Alert] Treffer heute ({now.date()})"
    msg["From"] = mail_from
    recipients = [addr.strip() for addr in to.split(',') if addr.strip()]
    msg["To"] = ", ".join(recipients)
    body = (
        "Guete Morge\n"
        f"Älplermagronen entdeckt: {', '.join(matches)}\n"
        f"Quelle: {url}\n\n"
        f"{snippet}"
    )
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(user, pw)
            smtp.send_message(msg)
        log("email sent")
    except Exception as e:
        log(f"email error: {e}")


def main() -> int:
    log("start")
    url = os.getenv("MENU_URL", "https://www.macchi-baeckerei.ch/menu.html")
    keywords_env = os.getenv("KEYWORDS")
    keywords = (
        [k.strip() for k in keywords_env.split(',') if k.strip()]
        if keywords_env
        else ["älplermagronen", "aelplermagronen", "alplermagronen"]
    )
    regex = os.getenv("KEYWORDS_REGEX")

    now = datetime.now(ZoneInfo("Europe/Zurich"))
    if not within_send_window(now):
        log("skip – outside send window")
        return 0

    try:
        log(f"fetch {url}")
        text = fetch_menu(url)
    except Exception as e:
        log(f"fetch error: {e}")
        return 0

    text = re.sub(r"\s+", " ", text)
    matches = find_matches(text, keywords, regex)
    if not matches:
        log("no match; exiting")
        return 0

    snippet = text[:600]
    send_email(matches, snippet, url, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
