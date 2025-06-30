import boto3
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any, Optional
import structlog
from ..core.config import settings

logger = structlog.get_logger(__name__)


class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

        self.llm = ChatBedrockConverse(
            model=settings.bedrock_model_id,
            max_tokens=settings.bedrock_max_tokens,
            temperature=settings.bedrock_temperature,
            client=self.client,
        )

        logger.info("Bedrock service initialized", model=settings.bedrock_model_id)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        try:
            langchain_messages = []

            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))

            if context:
                context_message = f"Context from relevant documents:\n{context}\n\n"
                langchain_messages.append(SystemMessage(content=context_message))

            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(SystemMessage(content=msg["content"]))

            response = await self.llm.ainvoke(langchain_messages)

            logger.info(
                "Generated response successfully",
                message_count=len(messages),
                response_length=len(response.content),
            )

            return response.content

        except Exception as e:
            logger.error("Error generating response", error=str(e))
            raise

    async def classify_intent(self, message: str) -> Dict[str, Any]:
        system_prompt = """
        You are an intent classification system. Analyze the user message and classify it into one of these categories:
        - question: User is asking a question about the Mexican Revolution
        - clarification: User is asking for clarification
        - follow_up: User is asking a follow-up question
        - summary_request: User wants a summary
        - escalation: User needs human assistance
        - off_topic: Question is not related to the Mexican Revolution
        
        Return ONLY a valid JSON response with this exact format:
        {
            "intent": "category",
            "confidence": 0.95,
            "entities": ["entity1", "entity2"]
        }
        
        Do not include any additional text, explanations, or formatting outside the JSON.
        """

        try:
            response = await self.generate_response(
                messages=[{"role": "user", "content": message}],
                system_prompt=system_prompt,
            )

            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = {"intent": "question", "confidence": 0.5, "entities": []}

            logger.info(
                "Intent classified",
                intent=result.get("intent"),
                confidence=result.get("confidence"),
            )
            return result

        except Exception as e:
            logger.error("Error classifying intent", error=str(e))
            return {"intent": "question", "confidence": 0.5, "entities": []}

    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        system_prompt = """
        You are a conversation summarizer. Create a concise summary of the conversation about the Mexican Revolution.
        Focus on the key topics discussed and main questions asked.
        Keep the summary under 200 words.
        """

        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in messages]
        )

        try:
            summary = await self.generate_response(
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this conversation:\n{conversation_text}",
                    }
                ],
                system_prompt=system_prompt,
            )

            logger.info("Conversation summarized", summary_length=len(summary))
            return summary

        except Exception as e:
            logger.error("Error summarizing conversation", error=str(e))
            return "Unable to generate summary at this time."

    async def check_content_safety(self, text: str) -> Dict[str, Any]:
        system_prompt = """
        You are a content safety checker. Evaluate if the text is appropriate and safe.
        Check for:
        - Harmful content
        - Inappropriate language
        - Offensive material
        
        Return ONLY a valid JSON response with this exact format:
        {
            "is_safe": true,
            "confidence": 0.95,
            "flags": ["flag1", "flag2"]
        }
        
        Do not include any additional text, explanations, or formatting outside the JSON.
        """

        try:
            response = await self.generate_response(
                messages=[
                    {"role": "user", "content": f"Check this text for safety:\n{text}"}
                ],
                system_prompt=system_prompt,
            )

            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = {"is_safe": True, "confidence": 0.5, "flags": []}

            logger.info("Content safety checked", is_safe=result.get("is_safe"))
            return result

        except Exception as e:
            logger.error("Error checking content safety", error=str(e))
            return {"is_safe": True, "confidence": 0.5, "flags": []}
