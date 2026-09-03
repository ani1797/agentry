#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deterministic calendar tiering, conflict resolution and slot search.

Reads one JSON document (stdin or a file) and emits either the list of
events that still need attendee data (stage ``triage``) or the full
prioritization plan (stage ``plan``).

Input document::

    {
      "timezone": "America/New_York",       # optional, default UTC
      "config": { ... },                    # see references/configuration.md
      "events": [ <graph event>, ... ],     # /me/calendarView value[]
      "attendees": { "<event id>": [ <graph attendee>, ... ] }   # optional
    }

Everything here is pure arithmetic on the fetched payload: no network,
no model judgment, same answer every run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from zoneinfo import ZoneInfo

DEFAULTS = {
    "company_domain": None,
    "manager_email": None,
    "skip_manager_email": None,
    "work_hours": "09:00-17:00",
    "work_days": "Mon,Tue,Wed,Thu,Fri",
    "lunch_window": "12:00-13:00",
    "breaks": ["10:00-10:15", "15:00-15:15"],
    "meeting_buffer": 5,
    "learning_keywords": [
        "office hours",
        "learning session",
        "brown bag",
        "lunch and learn",
        "training",
    ],
    "high_value_keywords": ["high-value", "customer-escalation", "escalation"],
    "protected_keywords": [
        "lunch",
        "break",
        "focus time",
        "focus block",
        "do not book",
        "no meetings",
        "blocked",
        "hold",
    ],
    "large_meeting_threshold": 15,
    "lunch_flex_minutes": 30,
}

TIER_LABELS = {
    0: "Protected block",
    1: "[EXT] Customer / external",
    2: "Manager / skip-manager",
    3: "Office hours / learning",
    4: "Internal high-value",
    5: "Internal routine",
}

TENTATIVE_NOTE = (
    "Kindly notifying you of a double-booked time slot. Here are some "
    "alternative times from my calendar: {times}. If rescheduling isn't "
    "possible and my attendance is required, please message me directly."
)

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# --------------------------------------------------------------------------
# parsing helpers


def parse_hhmm(value: str) -> dt.time:
    hour, minute = value.strip().replace(".", ":").split(":")[:2]
    return dt.time(int(hour), int(minute))


def parse_window(value: str) -> tuple[dt.time, dt.time]:
    """Parse ``09:00-17:00``; tolerates en/em dashes from hand-written config."""
    parts = re.split(r"\s*[-–—]\s*", value.strip())
    if len(parts) != 2:
        raise ValueError(f"expected a START-END window, got {value!r}")
    return parse_hhmm(parts[0]), parse_hhmm(parts[1])


def as_list(value, fallback):
    if value is None:
        return list(fallback)
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def load_config(raw: dict) -> dict:
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in (raw or {}).items() if v is not None})
    cfg["learning_keywords"] = [
        k.lower() for k in as_list(cfg["learning_keywords"], DEFAULTS["learning_keywords"])
    ]
    cfg["high_value_keywords"] = [
        k.lower() for k in as_list(cfg["high_value_keywords"], DEFAULTS["high_value_keywords"])
    ]
    cfg["protected_keywords"] = [
        k.lower() for k in as_list(cfg["protected_keywords"], DEFAULTS["protected_keywords"])
    ]
    cfg["work_days"] = [d[:3].title() for d in as_list(cfg["work_days"], DEFAULTS["work_days"])]
    cfg["breaks"] = as_list(cfg["breaks"], DEFAULTS["breaks"])
    cfg["meeting_buffer"] = int(cfg["meeting_buffer"])
    cfg["large_meeting_threshold"] = int(cfg["large_meeting_threshold"])
    cfg["lunch_flex_minutes"] = int(cfg["lunch_flex_minutes"])
    for key in ("company_domain", "manager_email", "skip_manager_email"):
        if cfg.get(key):
            cfg[key] = str(cfg[key]).strip().lower().lstrip("@")
    return cfg


def graph_dt(node: dict, tz: ZoneInfo, all_day: bool = False) -> dt.datetime:
    """Convert a Graph dateTimeTimeZone into the user's local zone.

    All-day events carry a midnight-UTC boundary that would otherwise land
    on the previous local day, so they are read as wall-clock dates.
    """
    raw = node["dateTime"].split(".")[0].rstrip("Z")
    naive = dt.datetime.fromisoformat(raw)
    if all_day:
        return naive.replace(tzinfo=tz)
    source = node.get("timeZone") or "UTC"
    try:
        origin = ZoneInfo("UTC" if source.upper() == "UTC" else source)
    except Exception:
        origin = ZoneInfo("UTC")
    return naive.replace(tzinfo=origin).astimezone(tz)


BOILERPLATE = re.compile(
    r"(microsoft teams|need help\?|join the meeting now|meeting id:|passcode:|"
    r"dial in by phone|find a local number|reset dial-in pin|for organizers:|"
    r"meeting options|join on your computer|zoom\.us/j/|________+|_____)",
    re.IGNORECASE,
)


def meeting_purpose(event: dict) -> tuple[str | None, str]:
    """Verbatim agenda from the invite body, minus join-link boilerplate.

    Returns ``(purpose, source)`` where source is ``verbatim`` when the
    organizer wrote something usable, or ``infer`` when the body is empty
    or pure conferencing boilerplate and the caller must infer intent.
    """
    body = event.get("bodyPreview") or ((event.get("body") or {}).get("content") or "")
    lines = []
    for line in re.split(r"[\r\n]+", str(body)):
        line = re.sub(r"<[^>]+>", " ", line)
        line = re.sub(r"https?://\S+", "", line).strip(" \t-*•")
        if not line or BOILERPLATE.search(line) or len(line) < 3:
            continue
        lines.append(re.sub(r"\s+", " ", line))
    text = " ".join(lines).strip()
    if len(text) < 8:
        return None, "infer"
    return (text[:240].rstrip() + "…" if len(text) > 240 else text), "verbatim"


def domain_of(address: str) -> str:
    return address.split("@")[-1].strip().lower() if "@" in (address or "") else ""


def attendee_addresses(event: dict) -> list[str]:
    out = []
    for att in event.get("attendees") or []:
        addr = ((att or {}).get("emailAddress") or {}).get("address")
        if addr:
            out.append(addr.strip().lower())
    organizer = ((event.get("organizer") or {}).get("emailAddress") or {}).get("address")
    if organizer:
        out.append(organizer.strip().lower())
    return out


# --------------------------------------------------------------------------
# classification


def is_blocking(event: dict) -> bool:
    """Informational rows (all-day PTO banners, free/tentative-holds) never conflict."""
    if event.get("isAllDay"):
        return False
    if (event.get("showAs") or "busy").lower() in {"free", "workingelsewhere", "unknown"}:
        return False
    response = ((event.get("responseStatus") or {}).get("response") or "").lower()
    return response != "declined"


def haystack(event: dict) -> str:
    return " ".join(
        [str(event.get("subject") or "")] + [str(c) for c in event.get("categories") or []]
    ).lower()


def classify(event: dict, cfg: dict) -> dict:
    """Assign a tier. Evaluated T0→T5; the first match wins."""
    text = haystack(event)
    addresses = attendee_addresses(event)
    domains = {domain_of(a) for a in addresses if domain_of(a)}
    company = cfg.get("company_domain")
    external_domains = sorted(d for d in domains if company and d != company)
    # Only a real attendees array proves internal-ness; organizer alone can
    # reveal an external meeting but never rule one out.
    loaded = event.get("attendees") is not None
    guests = len(event.get("attendees") or [])
    self_block = (
        any(k in text for k in cfg["protected_keywords"])
        and event.get("isOrganizer", True)
        and guests <= 1
    )

    reasons = []
    if self_block:
        tier, reason = 0, "personal protected block (lunch/break/focus)"
    elif external_domains:
        tier, reason = 1, f"external attendee domain: {', '.join(external_domains[:3])}"
    elif any(a in addresses for a in filter(None, [cfg.get("manager_email"), cfg.get("skip_manager_email")])):
        tier, reason = 2, "manager or skip-manager is an attendee"
    elif any(k in text for k in cfg["learning_keywords"]):
        tier, reason = 3, "matches learning_keywords"
    elif any(k in text for k in cfg["high_value_keywords"]):
        tier, reason = 4, "internal, flagged high-value"
    elif loaded:
        tier, reason = 5, "internal routine"
    else:
        tier, reason = 5, "provisional — attendee list not loaded"

    if not loaded and tier not in (0, 3):
        reasons.append("needs_attendees")
    if tier == 3:
        reasons.append("never_declined")
    if guests >= cfg["large_meeting_threshold"]:
        reasons.append("large_attendance")
    return {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "reason": reason,
        "external": bool(external_domains),
        "attendee_count": guests,
        "flags": reasons,
    }


def needs_attendees(event: dict, info: dict) -> bool:
    return "needs_attendees" in info["flags"] and not event.get("attendees")


# --------------------------------------------------------------------------
# schedule model


class Slot:
    def __init__(self, start: dt.datetime, end: dt.datetime, label: str, tier: int, kind: str):
        self.start, self.end, self.label, self.tier, self.kind = start, end, label, tier, kind

    def overlaps(self, other: "Slot") -> bool:
        return self.start < other.end and other.start < self.end


def protected_blocks(day: dt.date, cfg: dict, tz: ZoneInfo) -> list[Slot]:
    blocks = []
    windows = [("Lunch", cfg["lunch_window"])] + [
        (f"Break {i + 1}", w) for i, w in enumerate(cfg["breaks"])
    ]
    for label, window in windows:
        if not window:
            continue
        start_t, end_t = parse_window(window)
        blocks.append(
            Slot(
                dt.datetime.combine(day, start_t, tz),
                dt.datetime.combine(day, end_t, tz),
                label,
                0,
                "lunch" if label == "Lunch" else "break",
            )
        )
    return blocks


def free_slots(
    day: dt.date,
    busy: list[Slot],
    cfg: dict,
    tz: ZoneInfo,
    now: dt.datetime | None = None,
) -> list[tuple[dt.datetime, dt.datetime]]:
    if DAY_NAMES[day.weekday()] not in cfg["work_days"]:
        return []
    start_t, end_t = parse_window(cfg["work_hours"])
    cursor = dt.datetime.combine(day, start_t, tz)
    limit = dt.datetime.combine(day, end_t, tz)
    if now is not None:
        cursor = max(cursor, now)
    if cursor >= limit:
        return []
    gaps = []
    for slot in sorted((s for s in busy if s.end > cursor and s.start < limit), key=lambda s: s.start):
        if slot.start > cursor:
            gaps.append((cursor, min(slot.start, limit)))
        cursor = max(cursor, slot.end)
    if cursor < limit:
        gaps.append((cursor, limit))
    return [g for g in gaps if g[1] > g[0]]


def suggest_times(duration: dt.timedelta, days, busy_by_day, cfg, tz, limit=3, now=None):
    buffer = dt.timedelta(minutes=cfg["meeting_buffer"])
    needed = duration + buffer * 2
    out = []
    for day in days:
        for start, end in free_slots(day, busy_by_day.get(day, []), cfg, tz, now):
            if end - start >= needed:
                begin = start + buffer
                out.append(f"{begin:%a %b %-d %-I:%M %p}–{begin + duration:%-I:%M %p}")
            if len(out) >= limit:
                return out
    return out


def shift_lunch(lunch: Slot, blocker: Slot, cfg: dict) -> Slot | None:
    """Flex lunch up to ±lunch_flex_minutes to clear a T1/T2 call."""
    duration = lunch.end - lunch.start
    for minutes in range(5, cfg["lunch_flex_minutes"] + 1, 5):
        for delta in (dt.timedelta(minutes=minutes), dt.timedelta(minutes=-minutes)):
            moved = Slot(lunch.start + delta, lunch.start + delta + duration, lunch.label, 0, lunch.kind)
            if not moved.overlaps(blocker):
                return moved
    return None


# --------------------------------------------------------------------------
# main plan


def build_plan(doc: dict) -> dict:
    tz = ZoneInfo(doc.get("timezone") or "UTC")
    cfg = load_config(doc.get("config") or {})
    overlay = doc.get("attendees") or {}
    now = (
        dt.datetime.fromisoformat(doc["now"]).astimezone(tz)
        if doc.get("now")
        else None
    )

    events = []
    for raw in doc.get("events") or []:
        event = dict(raw)
        if event.get("id") in overlay and not event.get("attendees"):
            event["attendees"] = overlay[event["id"]]
        info = classify(event, cfg)
        all_day = bool(event.get("isAllDay"))
        start = graph_dt(event["start"], tz, all_day)
        end = graph_dt(event["end"], tz, all_day)
        purpose, purpose_source = meeting_purpose(event)
        events.append(
            {
                "id": event.get("id"),
                "subject": event.get("subject") or "(no subject)",
                "purpose": purpose,
                "purpose_source": purpose_source,
                "organizer": ((event.get("organizer") or {}).get("emailAddress") or {}).get("name"),
                "location": ((event.get("location") or {}).get("displayName") or None),
                "start": start,
                "end": end,
                "blocking": is_blocking(event),
                "raw": event,
                **info,
            }
        )
    events.sort(key=lambda e: (e["start"], e["tier"]))

    pending = [e["id"] for e in events if e["blocking"] and needs_attendees(e["raw"], e)]

    days = sorted({e["start"].date() for e in events})
    own_blocks = [
        Slot(e["start"], e["end"], e["subject"], 0, "own")
        for e in events
        if e["tier"] == 0 and e["blocking"]
    ]
    busy_by_day: dict[dt.date, list[Slot]] = {}
    protected: list[Slot] = []
    for day in days:
        # A real "Lunch" event on the calendar replaces the synthesized one.
        blocks = [
            b
            for b in protected_blocks(day, cfg, tz)
            if not any(b.overlaps(o) for o in own_blocks)
        ]
        protected += blocks
        busy_by_day[day] = list(blocks)
    for e in events:
        if e["blocking"]:
            busy_by_day.setdefault(e["start"].date(), []).append(
                Slot(e["start"], e["end"], e["subject"], e["tier"], "meeting")
            )

    # conflict clusters over blocking meetings only
    blocking = [e for e in events if e["blocking"]]
    clusters, current = [], []
    for e in blocking:
        if current and e["start"] < max(x["end"] for x in current):
            current.append(e)
        else:
            if len(current) > 1:
                clusters.append(current)
            current = [e]
    if len(current) > 1:
        clusters.append(current)

    if doc.get("_stage") == "triage":
        # Attendee data only changes the outcome for contested meetings and
        # anything touching a protected block; the rest is nice-to-have.
        contested = {e["id"] for c in clusters for e in c}
        for e in blocking:
            slot = Slot(e["start"], e["end"], "", e["tier"], "meeting")
            if any(slot.overlaps(b) for b in protected):
                contested.add(e["id"])
        return {
            "needs_attendees": [i for i in pending if i in contested],
            "needs_attendees_optional": [i for i in pending if i not in contested],
            "needs_purpose": [
                e["id"] for e in events if e["blocking"] and e["purpose_source"] == "infer"
            ],
            "event_count": len(events),
        }

    decisions = {e["id"]: {"action": "accept", "notes": []} for e in blocking}
    conflicts = []
    for cluster in clusters:
        # Greedy by priority: an event only yields to something it actually
        # overlaps, so a chain (A–B, B–C) never demotes C on A's behalf.
        ranked = sorted(cluster, key=lambda e: (e["tier"], e["start"], -e["attendee_count"]))
        accepted: list[dict] = []
        pairs: list[tuple[dict, dict]] = []
        for candidate in ranked:
            clash = next(
                (
                    a
                    for a in accepted
                    if candidate["start"] < a["end"] and a["start"] < candidate["end"]
                ),
                None,
            )
            if clash is None:
                accepted.append(candidate)
                continue
            pairs.append((clash, candidate))
            decision = decisions[candidate["id"]]
            decision["action"] = "tentative"
            large = "large_attendance" in candidate["flags"]
            never = "never_declined" in candidate["flags"] or large
            decision["notes"].append(f"Overlaps *{clash['subject']}* (T{clash['tier']}).")
            if never:
                decision["notes"].append(
                    "Kept on the calendar as tentative — office hours/learning and "
                    "large meetings are never declined or rescheduled."
                )
                if large:
                    decision["notes"].append(
                        f"Rescheduling is not feasible within 2 weeks ({candidate['attendee_count']} attendees)."
                    )
                decision["alternatives"] = []
                decision["message"] = None
            else:
                alts = suggest_times(
                    candidate["end"] - candidate["start"],
                    [d for d in days if d >= candidate["start"].date()],
                    busy_by_day,
                    cfg,
                    tz,
                    now=now,
                )
                decision["alternatives"] = alts
                decision["message"] = TENTATIVE_NOTE.format(
                    times=", ".join(alts) if alts else "none open in this window"
                )
        for kept, yielded in pairs:
            conflicts.append(
                {
                    "window": f"{yielded['start']:%a %b %-d %-I:%M %p}",
                    "kept": kept["id"],
                    "kept_subject": kept["subject"],
                    "kept_tier": kept["tier"],
                    "tentative": [yielded["id"]],
                    "tentative_subject": yielded["subject"],
                }
            )

    # protected blocks vs high-value calls
    lunch_actions = []
    for block in protected:
        clashes = [
            e
            for e in blocking
            if e["start"].date() == block.start.date()
            and Slot(e["start"], e["end"], "", e["tier"], "meeting").overlaps(block)
        ]
        high_value = [e for e in clashes if e["tier"] in (1, 2)]
        if block.kind == "lunch" and high_value:
            moved = shift_lunch(block, Slot(high_value[0]["start"], high_value[0]["end"], "", 1, "meeting"), cfg)
            lunch_actions.append(
                {
                    "block": block.label,
                    "date": f"{block.start:%a %b %-d}",
                    "reason": f"{high_value[0]['subject']} ({TIER_LABELS[high_value[0]['tier']]})",
                    "moved_to": f"{moved.start:%-I:%M %p}–{moved.end:%-I:%M %p}" if moved else None,
                    "note": None if moved else "Could not clear the call within ±%d min; lunch is squeezed." % cfg["lunch_flex_minutes"],
                }
            )
        elif clashes and block.kind != "lunch":
            lunch_actions.append(
                {
                    "block": block.label,
                    "date": f"{block.start:%a %b %-d}",
                    "reason": f"{clashes[0]['subject']} overlaps a protected block",
                    "moved_to": None,
                    "note": "Protected block held; the meeting is the one that yields.",
                }
            )

    # buffer violations between kept meetings
    buffer_violations = []
    kept = [e for e in blocking if decisions[e["id"]]["action"] == "accept"]
    for prev, nxt in zip(kept, kept[1:]):
        gap = (nxt["start"] - prev["end"]).total_seconds() / 60
        if 0 <= gap < cfg["meeting_buffer"]:
            buffer_violations.append(
                {
                    "after": prev["subject"],
                    "before": nxt["subject"],
                    "gap_minutes": int(gap),
                    "at": f"{nxt['start']:%a %b %-d %-I:%M %p}",
                }
            )

    return {
        "timezone": str(tz),
        "days": [str(d) for d in days],
        "needs_attendees": pending,
        "needs_purpose": [
            e["id"] for e in events if e["blocking"] and e["purpose_source"] == "infer"
        ],
        "meetings": [
            {
                "id": e["id"],
                "subject": ("[EXT] " if e["external"] else "") + e["subject"],
                "purpose": e["purpose"],
                "purpose_source": e["purpose_source"],
                "organizer": e["organizer"],
                "location": e["location"],
                "when": f"{e['start']:%a %b %-d %-I:%M %p}–{e['end']:%-I:%M %p}",
                "tier": e["tier"],
                "tier_label": e["tier_label"],
                "reason": e["reason"],
                "attendees": e["attendee_count"],
                "blocking": e["blocking"],
                "action": decisions.get(e["id"], {}).get("action", "informational"),
                "alternatives": decisions.get(e["id"], {}).get("alternatives", []),
                "message": decisions.get(e["id"], {}).get("message"),
                "notes": decisions.get(e["id"], {}).get("notes", []),
            }
            for e in events
        ],
        "conflicts": conflicts,
        "protected_blocks": lunch_actions,
        "buffer_violations": buffer_violations,
        "open_slots": {
            str(day): [
                f"{s:%-I:%M %p}–{e:%-I:%M %p}"
                for s, e in free_slots(day, busy_by_day.get(day, []), cfg, tz, now)
            ]
            for day in days
        },
    }


def render_markdown(plan: dict) -> str:
    lines = [f"## Calendar plan ({', '.join(plan['days'])}, {plan['timezone']})", ""]
    for m in plan["meetings"]:
        if not m["blocking"]:
            continue
        mark = {"accept": "keep", "tentative": "TENTATIVE"}.get(m["action"], m["action"])
        lines.append(f"- **{m['when']}** — {m['subject']} · T{m['tier']} {m['tier_label']} · {mark}")
        if m["purpose"]:
            lines.append(f"  - about: {m['purpose']}")
        else:
            lines.append(
                f"  - about: _no agenda in the invite — infer from subject, organizer "
                f"({m['organizer'] or 'unknown'}) and attendees_"
            )
        for note in m["notes"]:
            lines.append(f"  - {note}")
        if m["message"]:
            lines.append(f"  - reply: {m['message']}")
    if plan["conflicts"]:
        lines += ["", "### Conflicts"]
        for c in plan["conflicts"]:
            lines.append(f"- {c['window']}: kept *{c['kept_subject']}* (T{c['kept_tier']}); {len(c['tentative'])} marked tentative")
    if plan["protected_blocks"]:
        lines += ["", "### Protected blocks"]
        for b in plan["protected_blocks"]:
            target = f" → moved to {b['moved_to']}" if b["moved_to"] else ""
            lines.append(f"- {b['date']} {b['block']}{target} ({b['reason']}){' — ' + b['note'] if b['note'] else ''}")
    if plan["buffer_violations"]:
        lines += ["", "### Back-to-back"]
        for v in plan["buffer_violations"]:
            lines.append(f"- {v['at']}: only {v['gap_minutes']} min between *{v['after']}* and *{v['before']}*")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", nargs="?", default="-", help="JSON input file, or - for stdin")
    ap.add_argument("--stage", choices=["triage", "plan"], default="plan")
    ap.add_argument("--format", choices=["json", "markdown"], default="json")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    doc = json.loads(raw)
    doc["_stage"] = args.stage
    plan = build_plan(doc)
    if args.stage == "plan" and args.format == "markdown":
        print(render_markdown(plan))
    else:
        print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
