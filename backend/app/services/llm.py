"""
LangChain LLM singleton — lazily initialised on first call so that the
module can be imported without GOOGLE_API_KEY present (e.g. during tests
or cold imports).  The first actual call to get_llm() will raise clearly
if the key is missing.
"""

from __future__ import annotations
from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            # model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        )
    return _llm

