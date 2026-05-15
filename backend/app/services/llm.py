"""
LangChain ChatOpenAI singleton.
Model and API key are read from environment variables.
"""

from __future__ import annotations
from langchain_google_genai import ChatGoogleGenerativeAI

import os
# from langchain_openai import ChatOpenAI

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GOOGLE_API_KEY"))


def get_llm():
    global _llm
    # if _llm is None:
    #     _llm = ChatOpenAI(
    #         model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    #         temperature=0.2,         # low temperature reduces hallucinations
    #         api_key=os.getenv("OPENAI_API_KEY", os.getenv("API_KEY", "")),
    #     )
    return _llm

