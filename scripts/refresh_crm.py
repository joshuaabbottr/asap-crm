#!/usr/bin/env python3
"""Refresh CRM lead data from asappressurecleaning@gmail.com via Composio.

Reads the current ``index.html``, replaces the ``_RAW_LEADS`` array and the
``lastSync`` marker with fresh data pulled from Gmail (sent folder + inbox
reconciliation), and writes the file back.

Required env vars:
    COMPOSIO_API_KEY            Composio workspace API key
    COMPOSIO_GMAIL_ACCOUNT_ID   Connected account ID for the Gmail mailbox
                                (defaults to "gmail_anat-leon")
"""
from __future__ import annotations

import os
import re
import sys
import datetime
from collections import Counter
from pathlib import Path

import requests

API_KEY = os.environ.get("COMPOSIO_API_KEY")
ACCOUNT_ID = os.environ.get("COMPOSIO_GMAIL_ACCOUNT_ID", "gmail_anat-leon")
BASE_URL = "https://backend.composio.dev/api/v3"
SUBJECT_PREFIX = "Quick question about"

if not API_KEY:
    sys.exit("COMPOSIO_API_KEY env var is required")

HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}


def execute_tool(slug: str, args: dict) -> dict:
    """POST to the Composio v3 execute endpoint and return the response payload."""
    url = f"{BASE_URL}/tools/execute/{slug}"
    body = {
        "arguments": args,
        "connected_account_id": ACCOUNT_ID,
        "version": "latest",
    }
    r = requests.post(url, headers=HEADERS, json=body, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("successful", payload.get("data") is not None):
        raise RuntimeError(f"Composio call failed: {payload}")
    return payload.get("data", payload)


def fetch_all_pages(query: str, include_spam_trash: bool = False) -> list[dict]:
    """Page through GMAIL_FETCH_EMAILS for the given query and return every message."""
    out: list[dict] = []
    page_token: str | None = None
    while True:
        args: dict = {
            "query": query,
            "max_results": 100,
            "verbose": False,
            "include_payload": False,
            "include_spam_trash": include_spam_trash,
        }
        if page_token:
            args["page_token"] = page_token
        data = execute_tool("GMAIL_FETCH_EMAILS", args)
        msgs = data.get("messages") or []
        out.extend(msgs)
        page_token = data.get("nextPageToken") or None
        if not page_token:
            break
    return out


def classify(company: str, email: str) -> str:
    """Best-effort segment inference from the company name."""
    c = " " + company.lower() + " "
    saints = [
        " saint ", " st. ", " saint", "joan of arc", "therese", "ferrer",
        "paul of the cross", "francis of assisi", " patrick ", "john fisher",
        "immaculate", "pahokee", "rita ", "philip benizi", " luke ", " juliana ",
        " thomas more", " lucy ", " jude ", "john the evangelist", " mark ",
        " matthew ", " clare ", " peter ", " paul ", " mary ",
    ]
    church_kw = [
        " church", " catholic", " episcopal", " congregational", " lord ",
        " lady ", " trinity ", " cathedral", " basilica", " emmanuel ", " holy ",
        " sacred ", " temple ", " christ ", " jesus ", " fellowship", " alliance ",
        " ucc", " mission ", " parish", " ministry",
    ]
    if any(k in c for k in church_kw + saints) and "pressure" not in c:
        return "Churches"
    if "cremation" in c or "funeral" in c or "edgley" in c:
        return "Funeral Homes"
    if "yacht" in c or "marina" in c or "harbour" in c:
        return "Marinas"
    if (" golf " in c or "okeeheelee" in c or "osprey point" in c
            or "park ridge" in c or "southwinds" in c
            or "golf course" in c or "country club" in c):
        return "Golf Courses"
    if (" rv " in c or "rv resort" in c or "rv campground" in c
            or "rv park" in c or "campground" in c or "juno ocean walk" in c):
        return "RV Parks"
    if "storage" in c:
        return "Self-Storage Facilities"
    if "laundr" in c or " suds" in c:
        return "Laundromats"
    if ("car wash" in c or "mint eco" in c or "esteban brothers" in c
            or "auto spa" in c or "wash & wax" in c):
        return "Car Washes"
    if ("collision" in c or "paint & body" in c or "auto body" in c
            or "autobody" in c or "panoch auto" in c or "coachworks" in c
            or "auto care" in c or "auto collision" in c):
        return "Body Shops"
    if "auto group" in c or "dealer" in c:
        return "Auto Dealers"
    if "theatre" in c or "theater" in c or "cinema" in c or "playhouse" in c:
        return "Cinemas"
    if ("academy" in c or "preschool" in c or "school" in c
            or "learning center" in c or "kids academy" in c or "daycare" in c):
        return "Private Schools & Daycares"
    if ("assisted living" in c or "senior living" in c or "memory care" in c
            or "morselife" in c or "home care" in c or "alf" in c
            or "watercrest" in c or "palms edge" in c
            or "club at boynton" in c or "pb memory" in c):
        return "Assisted Living Facilities"
    if ("brewing" in c or "brewery" in c or "brewhouse" in c
            or "taproom" in c or "winery" in c):
        return "Wineries & Breweries"
    if ("animal" in c or " vet " in c or "vet " in c[:6]
            or "veterinary" in c or "paws" in c
            or "animal hospital" in c or "access specialty" in c):
        return "Veterinary Clinics"
    if "dental" in c or "dentistry" in c or "dentist" in c or "orthodont" in c:
        return "Dental Practices"
    if ("family practice" in c or "medical" in c or "primary care" in c
            or "chiropractor" in c or "rehab" in c
            or "la medical" in c or "sport & spinal" in c):
        return "Medical Offices"
    if ("fitness" in c or " gym " in c or "yoga" in c or "pilates" in c
            or "crossfit" in c or "loggerhead" in c):
        return "Fitness Centers / Gyms"
    if "ballroom" in c or "event hall" in c or "banquet" in c:
        return "Banquet / Event Venues"
    if (" hoa " in c or "property management" in c or "hawk-eye" in c
            or "lake charleston" in c or "davenport professional" in c
            or "propertymanager" in email):
        return "Apartment Buildings / HOA-governed properties"
    if "bowling" in c or " bowl " in c:
        return "Entertainment"
    if ("restaurant" in c or "cafe" in c or " bar " in c or "grille" in c
            or " grove" in c or "trattoria" in c or "el camino" in c
            or "salute" in c or "carmine" in c or "50 ocean" in c
            or "waterway" in c or "mamma mia" in c or "driftwood" in c
            or "banter" in c or "harrys" in c or "hugos" in c
            or "catering" in c or "modern restaurant" in c
            or " market" in c or "gourmet" in c or "rollatini" in c):
        return "Restaurants"
    return "Other"


def reconcile() -> tuple[list[dict], dict[str, int]]:
    """Return (leads, summary) reconciled from Gmail."""
    print("Fetching sent folder...", flush=True)
    sent = fetch_all_pages(f'in:sent subject:"{SUBJECT_PREFIX}"')
    if not sent:
        sys.exit("No sent emails found — check API key and connected account.")

    earliest_date = min(m["messageTimestamp"] for m in sent)[:10].replace("-", "/")
    print(f"Earliest send: {earliest_date}. Fetching inbox since...", flush=True)
    inbox = fetch_all_pages(
        f'(in:inbox OR in:spam) after:{earliest_date}',
        include_spam_trash=True,
    )

    bounce_threads: set[str] = set()
    delay_threads: set[str] = set()
    reply_threads: dict[str, str] = {}
    autoreply_threads: dict[str, str] = {}

    for m in inbox:
        sender = (m.get("sender") or "").lower()
        subject = m.get("subject") or ""
        thread_id = m.get("threadId")
        if not thread_id:
            continue
        if "mailer-daemon" in sender or "postmaster" in sender:
            if "Failure" in subject or "Undeliverable" in subject:
                bounce_threads.add(thread_id)
            elif "Delay" in subject:
                delay_threads.add(thread_id)
        elif subject.startswith("Automatic reply:"):
            autoreply_threads[thread_id] = "Auto-reply received"
        elif subject.lower().startswith("re: quick question about"):
            sender_name = (m.get("sender") or "").split("<")[0].strip().rstrip(" <")
            date = m.get("messageTimestamp", "")[:10]
            reply_threads[thread_id] = f"Reply from {sender_name} on {date}"

    leads: list[dict] = []
    seen_threads: set[str] = set()
    for m in sent:
        subject = m.get("subject") or ""
        if subject.lower().startswith("re: "):
            continue
        if not subject.startswith(SUBJECT_PREFIX):
            continue
        company = re.sub(rf"^{SUBJECT_PREFIX} ", "", subject)
        company = re.sub(r"'s building exterior$", "", company)
        company = re.sub(r"' building exterior$", "", company)
        company = re.sub(r"'$", "", company).strip()
        thread_id = m.get("threadId")
        if not thread_id or thread_id in seen_threads:
            continue
        seen_threads.add(thread_id)
        ts = m.get("messageTimestamp", "")
        to_field = (m.get("to") or "").strip()
        match = re.match(r".*<([^>]+)>", to_field)
        email = match.group(1) if match else to_field
        # Bucket by date — Apr 21 → c1, anything else → c2
        batch = "Apr21" if ts.startswith("2026-04-21") else "Apr22"
        seg = classify(company, email)
        stage = "Sent"
        notes_parts = [f"Sent:{ts[:10]}"]
        if thread_id in bounce_threads:
            stage = "Bounced"
            notes_parts.append("BOUNCED — undeliverable")
        elif thread_id in delay_threads:
            notes_parts.append("DELAY — still retrying")
        elif thread_id in reply_threads:
            stage = "Replied"
            notes_parts.append("REPLY: " + reply_threads[thread_id])
        elif thread_id in autoreply_threads:
            stage = "Opened"
            notes_parts.append(autoreply_threads[thread_id])
        leads.append({
            "id": thread_id,
            "company": company,
            "email": email,
            "segment": seg,
            "batch": batch,
            "stage": stage,
            "notes": " · ".join(notes_parts),
        })

    leads.sort(key=lambda l: (l["batch"], l["segment"], l["company"]))
    summary = dict(Counter(l["stage"] for l in leads))
    summary["total"] = len(leads)
    return leads, summary


def js_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def render_raw_leads(leads: list[dict]) -> str:
    rows = []
    for l in leads:
        rows.append(
            f'  ["{l["id"]}","{js_escape(l["company"])}","{js_escape(l["email"])}",'
            f'"{l["segment"]}","{l["batch"]}","{l["stage"]}","{js_escape(l["notes"])}"]'
        )
    return "const _RAW_LEADS = [\n" + ",\n".join(rows) + "\n];"


def update_html(leads: list[dict], path: Path = Path("index.html")) -> None:
    html = path.read_text(encoding="utf-8")

    new_block = render_raw_leads(leads)
    html_new, count = re.subn(
        r"const _RAW_LEADS = \[.*?\n\];",
        lambda _: new_block,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        sys.exit("Could not locate _RAW_LEADS array in index.html")

    today = datetime.date.today().strftime("%b %d, %Y").replace(" 0", " ")
    html_new = re.sub(
        r'<b id="lastSync">[^<]*</b>',
        f'<b id="lastSync">{today}</b>',
        html_new,
    )
    html_new = re.sub(
        r'<b id="lastSyncDetail">[^<]*</b>',
        f'<b id="lastSyncDetail">{today}</b>',
        html_new,
    )

    path.write_text(html_new, encoding="utf-8", newline="\n")


def main() -> None:
    leads, summary = reconcile()
    update_html(leads)
    print(f"Updated index.html with {summary['total']} leads")
    print(f"Stage breakdown: {summary}")


if __name__ == "__main__":
    main()
