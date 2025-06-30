from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
import re

from ..core.config import settings
from ..core.logging import logger


class RAGService:
    def __init__(self, bedrock_service, vector_store_service, memory_service, tools):
        self.bedrock_service = bedrock_service
        self.vector_store_service = vector_store_service
        self.memory_service = memory_service
        self.tools = tools

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        use_tools: bool = True,
    ) -> Dict[str, Any]:
        try:
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            conversation_messages = await self.memory_service.get_conversation_messages(
                conversation_id
            )

            safety_check = await self.bedrock_service.check_content_safety(message)
            if not safety_check.get("is_safe", True):
                response = "No puedo procesar este mensaje ya que puede contener contenido inapropiado."
                await self.memory_service.add_message(conversation_id, "user", message)
                await self.memory_service.add_message(
                    conversation_id, "assistant", response
                )

                return {
                    "response": response,
                    "conversation_id": conversation_id,
                    "sources": [],
                    "tools_used": ["content_safety_check"],
                    "confidence_score": 0.0,
                }

            intent_result = await self.bedrock_service.classify_intent(message)
            intent = intent_result.get("intent", "question")

            if intent == "escalation":
                escalation_id = None
                for msg in conversation_messages:
                    if (
                        msg.get("role") == "assistant"
                        and msg.get("content")
                        and "Escalation ID:" in msg["content"]
                    ):
                        match = re.search(
                            r"Escalation ID: ([a-f0-9\-]+)", msg["content"]
                        )
                        if match:
                            escalation_id = match.group(1)
                            break
                if escalation_id:
                    response = (
                        "Ya existe un caso de escalamiento para esta conversación. "
                        f"Escalation ID: {escalation_id}"
                    )
                    tools_used = ["human_escalation"]
                else:
                    response = "Entiendo que podrías necesitar asistencia humana. Permíteme escalar esta conversación por ti."
                    tools_used = ["human_escalation"]

                    escalation_tool = next(
                        (
                            tool
                            for tool in self.tools
                            if tool.name == "human_escalation"
                        ),
                        None,
                    )
                    if escalation_tool:
                        escalation_result = await escalation_tool.run(
                            conversation_id, "User requested escalation"
                        )
                        response += f" {escalation_result}"

            elif intent == "summary_request":
                response = "Voy a generar un resumen de nuestra conversación."
                tools_used = ["conversation_summary"]

                summary_tool = next(
                    (
                        tool
                        for tool in self.tools
                        if tool.name == "conversation_summary"
                    ),
                    None,
                )
                if summary_tool:
                    summary_result = await summary_tool.run(conversation_id)
                    response = summary_result

            elif intent == "off_topic":
                response, tools_used = await self._generate_rag_response(
                    message, conversation_messages, use_tools
                )
                if (
                    "I don't have enough information" in response
                    or "No relevant documents found" in response
                ):
                    response = "Solo puedo responder preguntas sobre la Revolución Mexicana basándome en los documentos proporcionados. Por favor, hazme una pregunta relacionada con este período histórico."
                    tools_used = []

            else:
                response, tools_used = await self._generate_rag_response(
                    message, conversation_messages, use_tools
                )

            await self.memory_service.add_message(conversation_id, "user", message)
            await self.memory_service.add_message(
                conversation_id, "assistant", response
            )

            confidence_score = intent_result.get("confidence", 0.5)

            return {
                "response": response,
                "conversation_id": conversation_id,
                "sources": [],
                "tools_used": tools_used,
                "confidence_score": confidence_score,
            }

        except Exception as e:
            error_response = f"Ocurrió un error al procesar tu mensaje: {str(e)}"

            if conversation_id:
                await self.memory_service.add_message(conversation_id, "user", message)
                await self.memory_service.add_message(
                    conversation_id, "assistant", error_response
                )

            return {
                "response": error_response,
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "sources": [],
                "tools_used": [],
                "confidence_score": 0.0,
            }

    async def _generate_rag_response(
        self, message: str, conversation_messages: List[Dict[str, Any]], use_tools: bool
    ) -> tuple[str, List[str]]:
        tools_used = []

        try:
            results = self.vector_store_service.similarity_search(message, k=3)
            context_chunks = []
            for doc in results:
                if isinstance(doc, dict) and "page_content" in doc:
                    context_chunks.append(str(doc["page_content"]))
                elif hasattr(doc, "page_content"):
                    context_chunks.append(str(doc.page_content))
                elif isinstance(doc, str):
                    context_chunks.append(doc)
            context = "\n\n".join(context_chunks)
            tools_used.append("document_search")
        except Exception as e:
            context = "No relevant documents found."
            logger.error(f"Error searching documents: {e}")

        conversation_context = ""
        if conversation_messages:
            recent_messages = conversation_messages[-6:]
            context_lines = []
            for msg in recent_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    role = "Usuario" if msg["role"] == "user" else "Asistente"
                    context_lines.append(f"{role}: {msg['content']}")
                elif isinstance(msg, str):
                    context_lines.append(msg)
            conversation_context = "\n".join(context_lines)

        system_prompt = f"""You are an expert assistant on the Mexican Revolution with conversation memory.

<context_documents>
{context}
</context_documents>

<conversation_history>
{conversation_context}
</conversation_history>

<instructions>
- MAXIMUM 2-3 sentences per answer
- NO more than 50 words
- Go STRAIGHT to the main point
- DO NOT use lists or bullet points
- DO NOT use phrases like "According to the provided context"
- Only say "I don't have enough information" if you can't answer
- IGNORE questions not related to the Mexican Revolution
- ALWAYS consider the conversation history for contextual answers
- If the question refers to something mentioned earlier, answer based on the history
</instructions>

<response_format>
Respond in a compact paragraph without introductions.
Example: "Porfirio Díaz ruled Mexico for 30 years until 1910. His dictatorship led to the Revolution when Madero called for armed rebellion."
</response_format>

<current_question>
{message}
</current_question>

ALWAYS answer in English if the question is in English, and in Spanish if the question is in Spanish.
Be EXTREMELY BRIEF considering the conversation context:"""

        response = await self.bedrock_service.generate_response(
            messages=[{"role": "user", "content": message}],
            context=context,
            system_prompt=system_prompt,
        )

        return response, tools_used

    async def get_conversation_history(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        return await self.memory_service.get_conversation_messages(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> bool:
        return await self.memory_service.delete_conversation(conversation_id)

    async def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        return await self.memory_service.get_conversation_summary(conversation_id)
