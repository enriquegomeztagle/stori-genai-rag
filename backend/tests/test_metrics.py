import pytest
from app.services.metrics_service import MetricsService


class TestMetricsService:
    @pytest.fixture
    def metrics_service(self):
        return MetricsService()

    @pytest.mark.asyncio
    async def test_record_response(self, metrics_service):
        response_id = await metrics_service.record_response(
            conversation_id="test-conv-1",
            query="When did the Mexican Revolution start?",
            response="The Mexican Revolution started in 1910.",
            response_time=1.5,
            confidence_score=0.85,
            tools_used=["vector_search", "conversation_summary"],
            sources_count=3,
            error_occurred=False,
        )

        assert response_id is not None
        assert len(metrics_service.response_metrics) == 1

        recorded_metric = metrics_service.response_metrics[0]
        assert recorded_metric.conversation_id == "test-conv-1"
        assert recorded_metric.query == "When did the Mexican Revolution start?"
        assert recorded_metric.response == "The Mexican Revolution started in 1910."
        assert recorded_metric.response_time == 1.5
        assert recorded_metric.confidence_score == 0.85
        assert recorded_metric.tools_used == ["vector_search", "conversation_summary"]
        assert recorded_metric.sources_count == 3
        assert recorded_metric.error_occurred == False

    @pytest.mark.asyncio
    async def test_record_user_rating(self, metrics_service):
        response_id = await metrics_service.record_response(
            conversation_id="test-conv-1",
            query="Test query",
            response="Test response",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=[],
            sources_count=1,
            error_occurred=False,
        )

        success = await metrics_service.record_user_rating(response_id, "like")
        assert success == True

        recorded_metric = metrics_service.response_metrics[0]
        assert recorded_metric.user_rating == "like"

        success = await metrics_service.record_user_rating(response_id, "dislike")
        assert success == True

        success = await metrics_service.record_user_rating("invalid-id", "like")
        assert success == False

    @pytest.mark.asyncio
    async def test_calculate_response_accuracy(self, metrics_service):
        accuracy = await metrics_service.calculate_response_accuracy(
            "When did the Mexican Revolution start?",
            "The Mexican Revolution started in 1910.",
        )
        assert accuracy == 1.0

        accuracy = await metrics_service.calculate_response_accuracy(
            "When did the Mexican Revolution start?",
            "The revolution began in the early 20th century.",
        )
        assert accuracy == 0.7

        accuracy = await metrics_service.calculate_response_accuracy(
            "When did the Mexican Revolution start?", "The weather is nice today."
        )
        assert accuracy == 0.3

        accuracy = await metrics_service.calculate_response_accuracy(
            "What is the weather like?", "It's sunny outside."
        )
        assert accuracy == 0.5

    @pytest.mark.asyncio
    async def test_get_system_metrics(self, metrics_service):
        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Test query 1",
            response="Test response 1",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=["tool1"],
            sources_count=1,
            error_occurred=False,
        )

        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Test query 2",
            response="Test response 2",
            response_time=2.0,
            confidence_score=0.9,
            tools_used=["tool1", "tool2"],
            sources_count=2,
            error_occurred=False,
        )

        await metrics_service.record_response(
            conversation_id="conv-2",
            query="Test query 3",
            response="Test response 3",
            response_time=0.5,
            confidence_score=0.7,
            tools_used=[],
            sources_count=0,
            error_occurred=True,
            error_message="Test error",
        )

        await metrics_service.record_user_rating(
            metrics_service.response_metrics[0].response_id, "like"
        )
        await metrics_service.record_user_rating(
            metrics_service.response_metrics[1].response_id, "like"
        )

        system_metrics = await metrics_service.get_system_metrics()

        assert system_metrics.total_queries == 3
        assert system_metrics.total_errors == 1
        assert round(system_metrics.average_response_time, 2) == 1.17
        assert system_metrics.like_percentage == 100.0
        assert abs(system_metrics.error_rate - 33.33) < 0.01
        assert system_metrics.conversation_retention_rate == 50.0

    @pytest.mark.asyncio
    async def test_conversation_metrics(self, metrics_service):
        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Query 1",
            response="Response 1",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=["tool1"],
            sources_count=1,
            error_occurred=False,
        )

        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Query 2",
            response="Response 2",
            response_time=1.5,
            confidence_score=0.9,
            tools_used=["tool2"],
            sources_count=2,
            error_occurred=False,
        )

        await metrics_service.record_response(
            conversation_id="conv-2",
            query="Query 3",
            response="Response 3",
            response_time=0.8,
            confidence_score=0.7,
            tools_used=[],
            sources_count=0,
            error_occurred=False,
        )

        await metrics_service.record_user_rating(
            metrics_service.response_metrics[0].response_id, "like"
        )
        await metrics_service.record_user_rating(
            metrics_service.response_metrics[1].response_id, "dislike"
        )

        conv_metrics = await metrics_service.get_conversation_metrics("conv-1")
        assert conv_metrics is not None
        assert conv_metrics.total_messages == 2
        assert conv_metrics.follow_up_questions == 1
        assert conv_metrics.average_response_time == 1.25
        assert conv_metrics.total_likes == 1
        assert conv_metrics.total_dislikes == 1
        assert conv_metrics.tools_usage_count["tool1"] == 1
        assert conv_metrics.tools_usage_count["tool2"] == 1

    @pytest.mark.asyncio
    async def test_recent_metrics(self, metrics_service):
        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Test query",
            response="Test response",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=[],
            sources_count=1,
            error_occurred=False,
        )

        recent_metrics = await metrics_service.get_recent_metrics(24)
        assert len(recent_metrics) == 1

        recent_metrics = await metrics_service.get_recent_metrics(1)
        assert len(recent_metrics) == 1

    @pytest.mark.asyncio
    async def test_clear_old_metrics(self, metrics_service):
        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Test query",
            response="Test response",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=[],
            sources_count=1,
            error_occurred=False,
        )

        assert len(metrics_service.response_metrics) == 1
        assert len(metrics_service.conversation_metrics) == 1

        await metrics_service.clear_old_metrics(1)

        assert len(metrics_service.response_metrics) == 1
        assert len(metrics_service.conversation_metrics) == 1

    @pytest.mark.asyncio
    async def test_export_metrics(self, metrics_service):
        await metrics_service.record_response(
            conversation_id="conv-1",
            query="Test query",
            response="Test response",
            response_time=1.0,
            confidence_score=0.8,
            tools_used=[],
            sources_count=1,
            error_occurred=False,
        )

        export_data = await metrics_service.export_metrics()

        assert "system_metrics" in export_data
        assert "conversation_metrics" in export_data
        assert "response_metrics" in export_data
        assert "export_timestamp" in export_data

        assert len(export_data["response_metrics"]) == 1
        assert len(export_data["conversation_metrics"]) == 1


TEST_QUERIES = [
    {
        "query": "When did the Mexican Revolution start?",
        "expected_answer": "1910",
        "test_responses": [
            ("The Mexican Revolution started in 1910.", 1.0),
            ("The revolution began in 1910.", 1.0),
            (
                "It started in the early 20th century, around 1910.",
                1.0,
            ),
            (
                "The Mexican Revolution began in the early 20th century.",
                0.7,
            ),
            ("The weather is nice today.", 0.3),
        ],
    },
    {
        "query": "Who was Pancho Villa?",
        "expected_answer": "revolutionary leader",
        "test_responses": [
            ("Pancho Villa was a revolutionary leader.", 1.0),
            ("He was a revolutionary general.", 0.7),
            ("Pancho Villa was a famous Mexican figure.", 0.3),
        ],
    },
]


@pytest.mark.asyncio
async def test_accuracy_validation():
    metrics_service = MetricsService()

    for test_case in TEST_QUERIES:
        for response, expected_accuracy in test_case["test_responses"]:
            accuracy = await metrics_service.calculate_response_accuracy(
                test_case["query"], response
            )
            assert (
                abs(accuracy - expected_accuracy) < 0.1
            ), f"Expected {expected_accuracy}, got {accuracy} for response: {response}"


if __name__ == "__main__":
    pytest.main([__file__])
