import unittest
from unittest.mock import Mock, patch

from bots import mega_bot


class SearchTests(unittest.TestCase):
    def test_search_returns_hacker_news_titles(self):
        response = Mock()
        response.json.return_value = {
            "hits": [{"title": "First story"}, {"title": "Second story"}]
        }

        with patch.object(mega_bot.requests, "get", return_value=response) as get:
            result = mega_bot.search("AI Engineering News", "AI agents")

        self.assertEqual(result, "First story\nSecond story")
        self.assertEqual(get.call_count, 1)
        self.assertEqual(get.call_args.kwargs["timeout"], 15)

    def test_github_topic_uses_repository_search_when_hacker_news_is_empty(self):
        hacker_news = Mock()
        hacker_news.json.return_value = {"hits": []}
        github = Mock()
        github.json.return_value = {
            "items": [
                {
                    "full_name": "example/agent",
                    "description": "An AI agent",
                    "stargazers_count": 42,
                }
            ]
        }

        with patch.object(
            mega_bot.requests, "get", side_effect=[hacker_news, github]
        ) as get:
            result = mega_bot.search("Trending AI Projects on GitHub Today", "AI")

        self.assertEqual(result, "example/agent - An AI agent - 42 stars")
        self.assertEqual(get.call_count, 2)
        self.assertEqual(
            get.call_args.kwargs["params"],
            {
                "q": "AI language:python",
                "sort": "stars",
                "order": "desc",
                "per_page": 5,
            },
        )

    def test_empty_search_uses_knowledge_fallback(self):
        response = Mock()
        response.json.return_value = {"hits": []}

        with patch.object(mega_bot.requests, "get", return_value=response):
            result = mega_bot.search("AI Engineering News", "AI news")

        self.assertEqual(
            result, "Use your own knowledge, today is 2026, give fresh news"
        )

    def test_hacker_news_error_uses_knowledge_fallback(self):
        with patch.object(
            mega_bot.requests, "get", side_effect=mega_bot.requests.Timeout()
        ):
            result = mega_bot.search("AI Engineering News", "AI news")

        self.assertEqual(
            result, "Use your own knowledge, today is 2026, give fresh news"
        )

    def test_github_error_uses_knowledge_fallback(self):
        hacker_news = Mock()
        hacker_news.json.return_value = {"hits": []}

        with patch.object(
            mega_bot.requests,
            "get",
            side_effect=[hacker_news, mega_bot.requests.Timeout()],
        ):
            result = mega_bot.search("Trending AI Projects on GitHub Today", "AI")

        self.assertEqual(
            result, "Use your own knowledge, today is 2026, give fresh news"
        )

    def test_empty_github_results_use_knowledge_fallback(self):
        hacker_news = Mock()
        hacker_news.json.return_value = {"hits": []}
        github = Mock()
        github.json.return_value = {"items": []}

        with patch.object(
            mega_bot.requests, "get", side_effect=[hacker_news, github]
        ):
            result = mega_bot.search("Trending AI Projects on GitHub Today", "AI")

        self.assertEqual(
            result, "Use your own knowledge, today is 2026, give fresh news"
        )


class SummaryTests(unittest.TestCase):
    def test_summary_uses_requested_news_expert_prompt(self):
        client = Mock()
        client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="🌟 خبر مهم"))
        ]

        result = mega_bot.summarize_topic(
            client,
            {"title": "AI Engineering News"},
            "Agent news and new tools",
        )

        self.assertEqual(result, "🌟 خبر مهم")
        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["model"], "llama-3.1-8b-instant")
        self.assertEqual(
            call["messages"][0]["content"],
            "You are a news expert. Topic: AI Engineering News. "
            "Info: Agent news and new tools. Give 3 real important news today "
            "in Moroccan Darija, 2 lines each, with emoji. If no info, give "
            "general important news in this field, never say 'no info'.",
        )

    def test_ntfy_sends_one_utf8_message(self):
        response = Mock()
        with patch.object(
            mega_bot.requests, "post", return_value=response
        ) as post:
            mega_bot.send_ntfy("خبر بالدارجة")

        self.assertEqual(post.call_count, 1)
        self.assertEqual(
            post.call_args.kwargs["data"], "خبر بالدارجة".encode("utf-8")
        )

    def test_main_sends_one_combined_report_for_all_topics(self):
        client = Mock()
        summarize = Mock(return_value="ملخص")
        fallback = "Use your own knowledge, today is 2026, give fresh news"
        with (
            patch.object(mega_bot, "GROQ_API_KEY", "test-key"),
            patch.object(mega_bot, "Groq", return_value=client),
            patch.object(mega_bot, "search", return_value=fallback),
            patch.object(mega_bot, "summarize_topic", summarize),
            patch.object(mega_bot, "send_ntfy") as send_ntfy,
            patch.object(mega_bot, "send_whatsapp"),
            patch.object(mega_bot.time, "sleep") as sleep,
        ):
            mega_bot.main()

        self.assertEqual(send_ntfy.call_count, 1)
        report = send_ntfy.call_args.args[0]
        for topic in mega_bot.TOPICS:
            self.assertIn(topic["title"], report)
        self.assertEqual(sleep.call_count, len(mega_bot.TOPICS) - 1)
        self.assertEqual(summarize.call_count, len(mega_bot.TOPICS))
        self.assertTrue(
            all(call.args[2] == fallback for call in summarize.call_args_list)
        )


if __name__ == "__main__":
    unittest.main()
