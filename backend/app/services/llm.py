"""
LiteLLM Router — lazily initialised on first call so the module can be
imported without GOOGLE_API_KEY present.  The router spreads load across
two Gemini models per feature group (summary / chat).

Environment variables
---------------------
GOOGLE_API_KEY or GEMINI_API_KEY   — required
SUMMARY_MODEL_1                    — default: gemini-3.1-flash-lite
SUMMARY_MODEL_2                    — default: gemini-2.5-flash-lite
CHAT_MODEL_1                       — default: gemini-3.1-flash-lite 
CHAT_MODEL_2                       — default: gemini-2.5-flash-lite
"""

from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv
from litellm import Router
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

load_dotenv()

_router: Router | None = None


def _build_router() -> Router:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    summary_models = [
        os.getenv("SUMMARY_MODEL_1", "gemini-3.1-flash-lite"),
        os.getenv("SUMMARY_MODEL_2", "gemini-2.5-flash-lite"),
    ]
    chat_models = [
        os.getenv("CHAT_MODEL_1", "gemini-3.1-flash-lite"),
        os.getenv("CHAT_MODEL_2", "gemini-2.5-flash-lite"),
    ]

    model_list = [
        *[
            {"model_name": "summary", "litellm_params": {"model": f"gemini/{m}", "api_key": api_key}}
            for m in summary_models
        ],
        *[
            {"model_name": "chat", "litellm_params": {"model": f"gemini/{m}", "api_key": api_key}}
            for m in chat_models
        ],
    ]

    return Router(model_list=model_list, routing_strategy="simple-shuffle")


def _get_router() -> Router:
    global _router
    if _router is None:
        _router = _build_router()
    return _router


def _to_litellm(messages: list[BaseMessage]) -> list[dict]:
    role_map = {SystemMessage: "system", HumanMessage: "user", AIMessage: "assistant"}
    out = []
    for m in messages:
        content = m.content if isinstance(m.content, str) else str(m.content)
        out.append({"role": role_map.get(type(m), "user"), "content": content})
    return out


class _RouterChatModel(BaseChatModel):
    """LangChain ChatModel backed by the LiteLLM Router."""

    model_group: str

    @property
    def _llm_type(self) -> str:
        return "litellm-router"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        resp = _get_router().completion(
            model=self.model_group, messages=_to_litellm(messages)
        )
        content = resp.choices[0].message.content or ""
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        resp = await _get_router().acompletion(
            model=self.model_group, messages=_to_litellm(messages)
        )
        content = resp.choices[0].message.content or ""
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


_summary_llm: _RouterChatModel | None = None
_chat_llm: _RouterChatModel | None = None


def get_summary_llm() -> _RouterChatModel:
    global _summary_llm
    if _summary_llm is None:
        _summary_llm = _RouterChatModel(model_group="summary")
    return _summary_llm


def get_chat_llm() -> _RouterChatModel:
    global _chat_llm
    if _chat_llm is None:
        _chat_llm = _RouterChatModel(model_group="chat")
    return _chat_llm
