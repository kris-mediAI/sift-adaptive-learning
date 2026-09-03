from core.resource_engine import ResourceEngine


class _FakeRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class _FakeSearch:
    def __init__(self, owner):
        self.owner = owner

    def list(self, **kwargs):
        self.owner.queries.append(kwargs["q"])
        response = self.owner.responses.pop(0)
        return _FakeRequest(response)


class _FakeYouTube:
    def __init__(self, responses):
        self.responses = list(responses)
        self.queries = []

    def search(self):
        return _FakeSearch(self)


def _item(video_id, title, description="", channel="Test Channel"):
    return {
        "id": {"videoId": video_id},
        "snippet": {
            "title": title,
            "description": description,
            "channelTitle": channel,
            "publishedAt": "2026-01-01T00:00:00Z",
            "thumbnails": {"high": {"url": f"https://img/{video_id}"}},
        },
    }


def test_composite_topic_accepts_strong_component_match():
    engine = ResourceEngine(youtube_api_key="test")
    score, reasons, rejected = engine._score_video(
        title="LangChain Tutorial for Beginners",
        description="Learn LangChain from scratch with practical examples.",
        concept="Generative AI and LangChain",
        subject="Machine Learning",
    )
    assert rejected is False
    assert score >= engine.MIN_VIDEO_SCORE
    assert any("component" in reason for reason in reasons)


def test_generic_component_does_not_pass():
    engine = ResourceEngine(youtube_api_key="test")
    score, reasons, rejected = engine._score_video(
        title="AI Tutorial for Beginners",
        description="An introduction to artificial intelligence.",
        concept="Generative AI and LangChain",
        subject="Machine Learning",
    )
    assert rejected is True
    assert score < engine.MIN_VIDEO_SCORE


def test_unrelated_video_still_rejected():
    engine = ResourceEngine(youtube_api_key="test")
    score, reasons, rejected = engine._score_video(
        title="Python String Operators Tutorial",
        description="Learn string manipulation and concatenation.",
        concept="modulo operator",
        subject="Python",
    )
    assert rejected is True
    assert score < engine.MIN_VIDEO_SCORE


def test_search_uses_fallback_only_when_first_query_has_no_accepted_result():
    engine = ResourceEngine(youtube_api_key="test")
    fake = _FakeYouTube(
        [
            {"items": [_item("bad", "Python Tutorial for Beginners", "Learn Python basics.")]},
            {"items": [_item("good", "LangChain Tutorial for Beginners", "Learn LangChain with examples.")]},
        ]
    )
    engine._youtube = fake

    results = engine.search_youtube(
        concept="Generative AI and LangChain",
        subject="Machine Learning",
        learner_level="Beginner",
        max_results=5,
    )

    assert len(results) == 1
    assert results[0]["video_id"] == "good"
    assert len(fake.queries) == 2
    assert "Generative AI and LangChain" in fake.queries[0]
    assert '"Generative AI and LangChain" tutorial explained' == fake.queries[1]


def test_search_stops_after_first_query_with_good_result():
    engine = ResourceEngine(youtube_api_key="test")
    fake = _FakeYouTube(
        [
            {"items": [_item("good", "Bayes Theorem Explained", "A tutorial on Bayes theorem.")]},
        ]
    )
    engine._youtube = fake

    results = engine.search_youtube(
        concept="Bayes theorem",
        subject="Mathematics",
        learner_level="Beginner",
        max_results=5,
    )

    assert results[0]["video_id"] == "good"
    assert len(fake.queries) == 1


def test_missing_key_is_explicit_but_does_not_break_recommendation_bundle():
    engine = ResourceEngine(youtube_api_key=None)
    payload = engine.recommend(
        concept="Generative AI and LangChain",
        subject="Machine Learning",
    )
    assert payload["youtube"] is None
    assert payload["youtube_status"] == "missing_api_key"
    assert "Generative+AI+and+LangChain" in payload["youtube_search_url"]
    assert payload["quick_tip"]["concept"] == "Generative AI and LangChain"
