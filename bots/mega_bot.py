"""Collect short updates for ten topics and send one combined report."""

import os
import sys
import time
from urllib.parse import quote

import requests
from groq import Groq


NTFY_TOPIC = os.getenv("NTFY_TOPIC") or "fes-ai-dizi-bots-4b"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DUCKDUCKGO_URL = "https://api.duckduckgo.com/"
GROQ_MODEL = "llama-3.1-8b-instant"

TOPICS = [
    {
        "id": "dizi_news_8am",
        "title": "Turkish Dizi Series News Today",
        "query": "Turkish dizi series news today",
    },
    {
        "id": "dizi_most_watched_9am",
        "title": "Most Watched Turkish Series Today",
        "query": "most watched Turkish TV series today",
    },
    {
        "id": "ai_courses_12pm",
        "title": "New Free AI Courses Today",
        "query": "new free artificial intelligence AI courses today",
    },
    {
        "id": "github_ai_2pm",
        "title": "Trending AI Projects on GitHub Today",
        "query": "trending AI projects GitHub today",
    },
    {
        "id": "scientific_movies_4pm",
        "title": "New Scientific Movies and Documentaries",
        "query": "new science movies documentaries today",
    },
    {
        "id": "ai_engineering_news_8pm",
        "title": "AI Engineering News: LLMs, Agents, RAG, MCP",
        "query": "AI engineering news LLM agents RAG MCP today",
    },
    {
        "id": "ai_arab_gulf_8pm",
        "title": "AI News: Arab World, Gulf, and Morocco",
        "query": "AI news Arab world Gulf Saudi UAE Qatar Morocco today",
    },
    {
        "id": "ai_global_8pm",
        "title": "Global AI News",
        "query": "AI news OpenAI Google Meta Anthropic today",
    },
    {
        "id": "ai_jobs_general_8pm",
        "title": "Worldwide Remote AI Jobs",
        "query": "remote AI jobs worldwide hiring today",
    },
    {
        "id": "ai_eng_jobs_gulf_8pm_midnight",
        "title": "AI Engineering Jobs in the Gulf",
        "query": "AI engineering jobs Dubai Riyadh Abu Dhabi today",
    },
]


def extract_search_text(data):
    """Collect useful text fields from DuckDuckGo's Instant Answer response."""
    parts = []

    for key in ("AbstractText", "Answer", "Definition"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    for key in ("Results", "RelatedTopics"):
        pending = list(data.get(key, [])) if isinstance(data.get(key), list) else []
        while pending:
            item = pending.pop()
            if not isinstance(item, dict):
                continue
            text = item.get("Text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
            children = item.get("Topics")
            if isinstance(children, list):
                pending.extend(children)

    return "\n".join(dict.fromkeys(parts))[:3000]


def search_topic(query):
    """Search DuckDuckGo and retry once when the request or response fails."""
    for attempt in range(2):
        try:
            response = requests.get(
                DUCKDUCKGO_URL,
                params={"q": query, "format": "json"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("DuckDuckGo returned an unexpected response")
            return extract_search_text(data)
        except (requests.RequestException, ValueError, TypeError) as error:
            print(f"Search attempt {attempt + 1} failed for '{query}': {error}")
            if attempt == 0:
                time.sleep(1)

    return ""


def summarize_topic(client, topic, search_text):
    """Ask Groq to summarize one topic in simple Moroccan Darija."""
    prompt = (
        "Summarize in 2 short lines in Moroccan Darija (Arabic dialect), "
        "simple words, one emoji at start.\n\n"
        f"Topic: {topic['title']}\n"
        f"Search results:\n{search_text}"
    )
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=120,
    )
    summary = response.choices[0].message.content
    if not summary or not summary.strip():
        raise ValueError("Groq returned an empty summary")
    return summary.strip()


def send_ntfy(message):
    """Send the combined report to ntfy without stopping the workflow on failure."""
    url = f"https://ntfy.sh/{quote(NTFY_TOPIC, safe='')}"
    try:
        response = requests.post(
            url,
            data=message.encode("utf-8"),
            headers={"Title": "Mega Bot Report", "Tags": "robot,ai"},
            timeout=30,
        )
        response.raise_for_status()
        print(f"Report sent to ntfy topic '{NTFY_TOPIC}'.")
    except requests.RequestException as error:
        print(f"Could not send the ntfy report: {error}")


def send_whatsapp(message):
    """Optionally send the first 900 report characters through CallMeBot."""
    phone = os.getenv("WHATSAPP_PHONE")
    api_key = os.getenv("CALLMEBOT_APIKEY")
    if not phone or not api_key:
        print("WhatsApp is not configured; skipping it.")
        return

    try:
        response = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={
                "phone": phone,
                "text": message[:900],
                "apikey": api_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        print("WhatsApp report sent.")
    except requests.RequestException as error:
        print(f"Could not send the WhatsApp report: {error}")


def main():
    """Run all topic searches, create one report, and send notifications."""
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is missing. Add it to the environment.", file=sys.stderr)
        raise SystemExit(1)

    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as error:
        print(f"ERROR: Could not start the Groq client: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    report_parts = ["Fes AI Mega Bot Report"]
    for index, topic in enumerate(TOPICS):
        print(f"Processing {index + 1}/{len(TOPICS)}: {topic['title']}")
        try:
            search_text = search_topic(topic["query"])
            if not search_text:
                summary = "⚠️ ما لقيناش معلومات كافية لهاد الموضوع دابا."
            else:
                summary = summarize_topic(client, topic, search_text)
        except Exception as error:
            print(f"Topic failed ({topic['id']}): {error}")
            summary = "⚠️ تعذر إعداد الملخص لهاد الموضوع دابا."

        report_parts.extend([f"{topic['title']}\n{summary}", "---"])
        if index < len(TOPICS) - 1:
            time.sleep(1)

    full_message = "\n".join(report_parts)
    send_ntfy(full_message)
    send_whatsapp(full_message)


if __name__ == "__main__":
    main()
