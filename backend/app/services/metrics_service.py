import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio
from collections import defaultdict

from ..core.logging import logger


@dataclass
class ResponseMetrics:

    response_id: str
    conversation_id: str
    query: str
    response: str
    response_time: float
    confidence_score: float
    tools_used: List[str]
    sources_count: int
    timestamp: datetime
    user_rating: Optional[str] = None
    error_occurred: bool = False
    error_message: Optional[str] = None


@dataclass
class ConversationMetrics:

    conversation_id: str
    total_messages: int
    follow_up_questions: int
    context_retention_score: float
    average_response_time: float
    total_likes: int
    total_dislikes: int
    tools_usage_count: Dict[str, int]
    created_at: datetime
    last_activity: datetime


@dataclass
class SystemMetrics:

    total_queries: int
    total_errors: int
    average_response_time: float
    like_percentage: float
    tool_effectiveness: Dict[str, float]
    error_rate: float
    conversation_retention_rate: float
    timestamp: datetime


class MetricsService:

    def __init__(self):
        self.response_metrics: List[ResponseMetrics] = []
        self.conversation_metrics: Dict[str, ConversationMetrics] = {}
        self.system_metrics: Optional[SystemMetrics] = None
        self.test_queries: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        self._initialize_test_queries()

    def _initialize_test_queries(self):
        self.test_queries = {
            "mexican_revolution_start": {
                "query": "When did the Mexican Revolution start?",
                "expected_answer": "1910",
                "keywords": ["1910", "revolution", "start", "begin"],
            },
            "pancho_villa": {
                "query": "Who was Pancho Villa?",
                "expected_answer": "revolutionary leader",
                "keywords": ["revolutionary", "leader", "general", "dorado"],
            },
            "emiliano_zapata": {
                "query": "What was Emiliano Zapata known for?",
                "expected_answer": "land reform",
                "keywords": ["land", "reform", "agrarian", "peasant"],
            },
        }

    async def record_response(
        self,
        conversation_id: str,
        query: str,
        response: str,
        response_time: float,
        confidence_score: float,
        tools_used: List[str],
        sources_count: int,
        error_occurred: bool = False,
        error_message: Optional[str] = None,
    ) -> str:
        async with self._lock:
            response_id = str(uuid.uuid4())

            metrics = ResponseMetrics(
                response_id=response_id,
                conversation_id=conversation_id,
                query=query,
                response=response,
                response_time=response_time,
                confidence_score=confidence_score,
                tools_used=tools_used,
                sources_count=sources_count,
                timestamp=datetime.utcnow(),
                error_occurred=error_occurred,
                error_message=error_message,
            )

            self.response_metrics.append(metrics)

            await self._update_conversation_metrics(conversation_id, metrics)

            logger.info(
                "Response metrics recorded",
                response_id=response_id,
                conversation_id=conversation_id,
                response_time=response_time,
                confidence_score=confidence_score,
            )

            return response_id

    async def record_user_rating(self, response_id: str, rating: str) -> bool:
        async with self._lock:
            for metrics in self.response_metrics:
                if metrics.response_id == response_id:
                    metrics.user_rating = rating

                    await self._update_conversation_metrics(
                        metrics.conversation_id, metrics
                    )

                    logger.info(
                        "User rating recorded", response_id=response_id, rating=rating
                    )
                    return True

            return False

    async def _update_conversation_metrics(
        self, conversation_id: str, response_metrics: ResponseMetrics
    ):
        if conversation_id not in self.conversation_metrics:
            self.conversation_metrics[conversation_id] = ConversationMetrics(
                conversation_id=conversation_id,
                total_messages=0,
                follow_up_questions=0,
                context_retention_score=0.0,
                average_response_time=0.0,
                total_likes=0,
                total_dislikes=0,
                tools_usage_count=defaultdict(int),
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

        conv_metrics = self.conversation_metrics[conversation_id]
        conv_metrics.total_messages += 1
        conv_metrics.last_activity = datetime.utcnow()

        for tool in response_metrics.tools_used:
            conv_metrics.tools_usage_count[tool] += 1

        if response_metrics.user_rating == "like":
            conv_metrics.total_likes += 1
        elif response_metrics.user_rating == "dislike":
            conv_metrics.total_dislikes += 1

        if conv_metrics.total_messages > 1:
            conv_metrics.follow_up_questions += 1

        conversation_responses = [
            rm for rm in self.response_metrics if rm.conversation_id == conversation_id
        ]
        if conversation_responses:
            conv_metrics.average_response_time = sum(
                rm.response_time for rm in conversation_responses
            ) / len(conversation_responses)

    async def calculate_response_accuracy(self, query: str, response: str) -> float:
        query_lower = query.lower()
        response_lower = response.lower()

        for test_id, test_data in self.test_queries.items():
            if any(keyword in query_lower for keyword in test_data["keywords"]):
                expected_answer = test_data["expected_answer"].lower()

                if expected_answer in response_lower:
                    return 1.0
                elif any(
                    keyword in response_lower for keyword in test_data["keywords"]
                ):
                    return 0.7
                else:
                    return 0.3

        return 0.5

    async def get_system_metrics(self) -> SystemMetrics:
        async with self._lock:
            if not self.response_metrics:
                return SystemMetrics(
                    total_queries=0,
                    total_errors=0,
                    average_response_time=0.0,
                    like_percentage=0.0,
                    tool_effectiveness={},
                    error_rate=0.0,
                    conversation_retention_rate=0.0,
                    timestamp=datetime.utcnow(),
                )

            total_queries = len(self.response_metrics)
            total_errors = sum(1 for rm in self.response_metrics if rm.error_occurred)
            average_response_time = (
                sum(rm.response_time for rm in self.response_metrics) / total_queries
            )

            rated_responses = [rm for rm in self.response_metrics if rm.user_rating]
            if rated_responses:
                likes = sum(1 for rm in rated_responses if rm.user_rating == "like")
                like_percentage = (likes / len(rated_responses)) * 100
            else:
                like_percentage = 0.0

            tool_usage = defaultdict(int)
            tool_ratings = defaultdict(list)

            for rm in self.response_metrics:
                for tool in rm.tools_used:
                    tool_usage[tool] += 1
                    if rm.user_rating:
                        tool_ratings[tool].append(rm.user_rating)

            tool_effectiveness = {}
            for tool, ratings in tool_ratings.items():
                if ratings:
                    likes = sum(1 for r in ratings if r == "like")
                    tool_effectiveness[tool] = (likes / len(ratings)) * 100
                else:
                    tool_effectiveness[tool] = 0.0

            error_rate = (
                (total_errors / total_queries) * 100 if total_queries > 0 else 0.0
            )

            if self.conversation_metrics:
                conversations_with_followups = sum(
                    1
                    for cm in self.conversation_metrics.values()
                    if cm.follow_up_questions > 0
                )
                conversation_retention_rate = (
                    conversations_with_followups / len(self.conversation_metrics)
                ) * 100
            else:
                conversation_retention_rate = 0.0

            self.system_metrics = SystemMetrics(
                total_queries=total_queries,
                total_errors=total_errors,
                average_response_time=average_response_time,
                like_percentage=like_percentage,
                tool_effectiveness=tool_effectiveness,
                error_rate=error_rate,
                conversation_retention_rate=conversation_retention_rate,
                timestamp=datetime.utcnow(),
            )

            return self.system_metrics

    async def get_conversation_metrics(
        self, conversation_id: str
    ) -> Optional[ConversationMetrics]:
        return self.conversation_metrics.get(conversation_id)

    async def get_all_conversation_metrics(self) -> List[ConversationMetrics]:
        return list(self.conversation_metrics.values())

    async def get_response_metrics(self, response_id: str) -> Optional[ResponseMetrics]:
        for metrics in self.response_metrics:
            if metrics.response_id == response_id:
                return metrics
        return None

    async def get_recent_metrics(self, hours: int = 24) -> List[ResponseMetrics]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [rm for rm in self.response_metrics if rm.timestamp >= cutoff_time]

    async def clear_old_metrics(self, days: int = 30):
        async with self._lock:
            if days == 0:
                self.response_metrics = []
                self.conversation_metrics = {}
                logger.info("Cleared all metrics")
            else:
                cutoff_time = datetime.utcnow() - timedelta(days=days)

                self.response_metrics = [
                    rm for rm in self.response_metrics if rm.timestamp >= cutoff_time
                ]

                self.conversation_metrics = {
                    conv_id: conv_metrics
                    for conv_id, conv_metrics in self.conversation_metrics.items()
                    if conv_metrics.last_activity >= cutoff_time
                }

                logger.info(f"Cleared metrics older than {days} days")

    async def export_metrics(self) -> Dict[str, Any]:
        system_metrics = await self.get_system_metrics()

        return {
            "system_metrics": asdict(system_metrics),
            "conversation_metrics": [
                asdict(cm) for cm in self.conversation_metrics.values()
            ],
            "response_metrics": [asdict(rm) for rm in self.response_metrics],
            "export_timestamp": datetime.utcnow().isoformat(),
        }
