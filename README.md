# Fes AI Mega Bot

A small Python bot that gathers updates for 10 topics, summarizes them in
Moroccan Darija with Groq, and sends one combined report to ntfy.sh. GitHub
Actions runs it while your computer is off.

## What it does

- Searches each topic with the DuckDuckGo Instant Answer API.
- Summarizes results with Groq's `llama-3.1-8b-instant` model.
- Sends one report to your ntfy topic.
- Optionally sends the first 900 characters through CallMeBot for WhatsApp.
- Runs daily at 08:00, 12:00, and 20:00 UTC, or manually from GitHub Actions.

Each scheduled run includes all 10 topics. DuckDuckGo's Instant Answer API
does not always return current or detailed results, so some summaries may say
that information was unavailable.

## Setup on GitHub

1. Create a new GitHub repository named `fes-ai-dizi-bots-4b`.
2. Add these project files to the repository and push them to GitHub.
3. Open **Settings > Secrets and variables > Actions** and add repository
   secrets:
   - `GROQ_API_KEY` — required; create a key in the Groq console.
   - `NTFY_TOPIC` — optional; defaults to `fes-ai-dizi-bots-4b`.
   - `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` — optional; both are needed for
     WhatsApp notifications.
4. On your phone, install ntfy and subscribe to the topic
   `fes-ai-dizi-bots-4b` (or the value you put in `NTFY_TOPIC`).
5. Open the repository's **Actions** tab, choose **mega_bot**, then select
   **Run workflow** to test it.

Make sure GitHub Actions is enabled for the repository. Scheduled runs use
UTC and GitHub may start them a little later than the exact cron time.

## Privacy and free-tier notes

ntfy topics are public: anyone who knows a topic name can subscribe to it or
send messages to it. Do not include private information in your reports. You
can set `NTFY_TOPIC` to a less guessable name.

The project uses free-tier services, but Groq, GitHub Actions, and
CallMeBot can have usage limits or terms that change over time. WhatsApp is
optional; the bot works without it.

## المغربيّة بالدارجة

هاد البوت كيجمع معلومات على 10 مواضيع، وكيختاصرها بالدارجة باستعمال Groq،
ومن بعد كيبعث تقرير واحد لتطبيق ntfy. GitHub Actions كيشغلو حتى إلا كان
الكمبيوتر ديالك طافي.

### كيفاش تبدا

1. صايب repository جديد فـ GitHub بالاسم `fes-ai-dizi-bots-4b`، وحط فيه
   ملفات هاد المشروع.
2. دخل لـ **Settings > Secrets and variables > Actions** وزيد:
   - `GROQ_API_KEY` ضروري: جيب المفتاح من Groq console.
   - `NTFY_TOPIC` اختياري: إلا ما زدتيهش غادي يستعمل
     `fes-ai-dizi-bots-4b`.
   - `WHATSAPP_PHONE` و `CALLMEBOT_APIKEY` اختياريين إلا بغيتي رسائل
     WhatsApp عبر CallMeBot.
3. فالتليفون، نزّل ntfy وsubscribe للموضوع
   `fes-ai-dizi-bots-4b` (ولا الاسم اللي حطيتي فـ `NTFY_TOPIC`).
4. دخل لـ **Actions**، اختار **mega_bot**، ومن بعد **Run workflow** باش
   تجرب البوت.

كل تشغيل مبرمج كيجمع المواضيع العشرة كاملين. المواعيد هي 08:00 و12:00
و20:00 بتوقيت UTC، وممكن GitHub يتأخر شوية فبداية التشغيل. API ديال
DuckDuckGo مرات ما كيرجعش معلومات جديدة أو كافية.

تنبيه: مواضيع ntfy عموميين؛ أي واحد عارف الاسم يقدر يشوف الرسائل. ما تحطش
معلومات خاصة فالتقرير، واستعمل اسم صعيب التخمين إلا احتجتي خصوصية أكثر.
