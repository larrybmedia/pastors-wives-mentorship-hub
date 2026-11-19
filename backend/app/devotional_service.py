
import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.parse import quote
from datetime import datetime, date
from zoneinfo import ZoneInfo

from groq import Groq
from sqlalchemy import select

from . import db
from .models import Devotional

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo(
    os.getenv("TIMEZONE", "Africa/Lagos")
)

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def nigeria_today():
    return datetime.now(TIMEZONE).date()


def generate_devotional(target_date=None):
    """
    Generate and save one unpublished devotional.
    An existing devotional for the date is never overwritten.
    """

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured.")

    target_date = target_date or nigeria_today()
    devotional_date = target_date.isoformat()

    # Prevent duplicate generation.
    existing = db.session.execute(
        select(Devotional).where(
            Devotional.date == devotional_date
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    prompt = f"""
You are a thoughtful Christian devotional writer
serving a community of pastors' wives.

Prepare a biblically grounded daily devotional for:
{devotional_date}

The devotional should be warm, spiritually mature,
practical, encouraging and sensitive to the unique
experiences of women serving in ministry.

Address faith, marriage, family, leadership,
personal growth, emotional well-being, service,
purpose and relationship with God where appropriate.

Return ONLY valid JSON with these fields:

{{
  "title": "A meaningful devotional title",
  "theme": "The central spiritual theme",
  "reference": "Bible book, chapter and verse",
  "verse": "A short scripture quotation or passage identification",
  "reflection": "A thoughtful and substantial reflection",
  "application": "Practical application to everyday life",
  "prayer": "A sincere and meaningful prayer",
  "action": "One practical action for today"
}}

IMPORTANT:
- Never invent Bible quotations.
- Provide an accurate scripture reference.
- If exact quotation cannot be verified, provide the
  reference and mark the verse for verified-text insertion.
- Do not include markdown fences.
- Return valid JSON only.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write Christian devotionals for pastors' wives. "
                    "Always return one valid JSON object. "
                    "Do not use markdown or text outside the JSON object. "
                    "All eight requested fields must be strings."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=2500,
        response_format={"type": "json_object"}
    )

    raw_content = response.choices[0].message.content

    if not raw_content:
        raise ValueError("Groq returned an empty devotional response.")

    try:
        content = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        logger.error("Invalid Groq JSON response: %s", raw_content)
        raise ValueError("Groq returned invalid JSON.") from exc

    required = [
        "title",
        "theme",
        "reference",
        "verse",
        "reflection",
        "application",
        "prayer",
        "action"
    ]

    for field in required:
        if not isinstance(content.get(field), str) or not content[field].strip():
            raise ValueError(
                f"Invalid devotional field: {field}"
            )

    devotional = Devotional(
        date=devotional_date,
        title=content["title"],
        theme=content["theme"],
        reference=content["reference"],
        verse=content["verse"],
        reflection=content["reflection"],
        application=content["application"],
        prayer=content["prayer"],
        action=content["action"],
        published=False,
        generated_by="groq"
    )

    db.session.add(devotional)
    db.session.commit()

    logger.info(
        "Generated devotional for %s",
        devotional_date
    )

    return devotional


def verify_scripture(reference):
    """Retrieve the exact KJV passage for a Bible reference."""

    url = (
        "https://bible-api.com/"
        + quote(reference, safe="")
        + "?translation=kjv"
    )

    request = Request(
        url,
        headers={"User-Agent": "PastorsWivesMentorshipHub/1.0"}
    )

    with urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if result.get("translation_name") != "King James Version":
        raise ValueError("KJV Scripture verification failed.")

    verified_text = (result.get("text") or "").strip()
    verified_reference = (result.get("reference") or "").strip()

    if not verified_text or not verified_reference:
        raise ValueError("No verified Scripture text was returned.")

    return verified_reference, verified_text


def publish_devotional(target_date=None):
    """Verify Scripture and publish only after successful verification."""

    target_date = target_date or nigeria_today()

    devotional = db.session.execute(
        select(Devotional).where(
            Devotional.date == target_date.isoformat()
        )
    ).scalar_one_or_none()

    if not devotional:
        devotional = generate_devotional(target_date)

    # Fail closed: do not publish if the reference cannot be verified.
    verified_reference, verified_text = verify_scripture(
        devotional.reference
    )

    devotional.reference = verified_reference
    devotional.verse = verified_text
    devotional.published = True
    db.session.commit()

    logger.info(
        "Verified KJV Scripture and published devotional for %s",
        target_date.isoformat()
    )

    return devotional


def prepare_tomorrow():
    """
    Generate tomorrow's devotional ahead of publication.
    """

    tomorrow = date.fromordinal(
        nigeria_today().toordinal() + 1
    )

    return generate_devotional(tomorrow)
