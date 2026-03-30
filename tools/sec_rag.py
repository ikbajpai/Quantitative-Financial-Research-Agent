"""
SEC 10-K Filing RAG Tool.
Fetches the latest 10-K from SEC EDGAR, chunks the Risk Factors (1A) and
MD&A (Item 7) sections, indexes them in FAISS, and answers analyst queries.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

EDGAR_HEADERS = {"User-Agent": "QuantFinanceResearchAgent research@example.com"}
CACHE_DIR = Path.home() / ".quant-agent" / "sec_cache"
SECTIONS_OF_INTEREST = ["risk factors", "management", "results of operations", "liquidity"]


class SECFilingInput(BaseModel):
    ticker: str = Field(description="Company ticker symbol (e.g. 'AAPL', 'MSFT')")
    query: str = Field(
        description=(
            "What to look for in the filing. Examples: "
            "'What are the main risk factors?', "
            "'What does management say about AI competition?', "
            "'What is the revenue growth outlook?'"
        )
    )
    form_type: str = Field(
        default="10-K",
        description="SEC form type: '10-K' (annual) or '10-Q' (quarterly)",
    )


def _get_cik(ticker: str) -> Optional[str]:
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&forms=10-K"
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{ticker}"', "forms": "10-K"},
            headers=EDGAR_HEADERS,
            timeout=10,
        )
        hits = resp.json().get("hits", {}).get("hits", [])
        if hits:
            return hits[0].get("_source", {}).get("entity_id")
    except Exception as e:
        logger.warning("CIK lookup failed for %s: %s", ticker, e)

    try:
        resp = requests.get(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            params={"company": ticker, "CIK": ticker, "type": "10-K", "action": "getcompany", "output": "atom"},
            headers=EDGAR_HEADERS,
            timeout=10,
        )
        match = re.search(r"CIK=(\d+)", resp.text)
        if match:
            return match.group(1).zfill(10)
    except Exception as e:
        logger.warning("EDGAR browse fallback failed: %s", e)

    return None


def _get_latest_filing_url(cik: str, form_type: str = "10-K") -> Optional[str]:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
        data = resp.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if form == form_type:
                accession = accession_numbers[i].replace("-", "")
                doc = primary_docs[i]
                return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{doc}"
    except Exception as e:
        logger.warning("Filing URL lookup failed for CIK %s: %s", cik, e)
    return None


def _fetch_filing_text(url: str) -> Optional[str]:
    try:
        time.sleep(0.5)
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        content_type = resp.headers.get("content-type", "")
        if "html" in content_type or url.endswith(".htm") or url.endswith(".html"):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.content, "lxml")
            for tag in soup(["script", "style", "table"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
        else:
            text = resp.text

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        logger.error("Failed to fetch filing text: %s", e)
        return None


def _extract_relevant_sections(text: str, max_chars: int = 40000) -> str:
    text_lower = text.lower()
    sections = []

    patterns = [
        (r"item\s*1a[\.\s]+risk factors", r"item\s*1b"),
        (r"item\s*7[\.\s]+management", r"item\s*7a"),
        (r"results of operations", r"liquidity and capital"),
    ]

    for start_pattern, end_pattern in patterns:
        start_match = re.search(start_pattern, text_lower)
        if start_match:
            end_match = re.search(end_pattern, text_lower[start_match.start():])
            if end_match:
                section_text = text[start_match.start(): start_match.start() + end_match.start()]
                sections.append(section_text[:15000])
            else:
                sections.append(text[start_match.start(): start_match.start() + 15000])

    if sections:
        combined = "\n\n---\n\n".join(sections)
        return combined[:max_chars]

    return text[:max_chars]


def _build_rag_response(text: str, query: str, ticker: str) -> str:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain.chat_models import init_chat_model
        from langchain_core.messages import HumanMessage

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_text(text)

        if not chunks:
            return json.dumps({"error": "No text chunks extracted from filing."})

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        vectorstore = FAISS.from_texts(chunks, embeddings)
        relevant_docs = vectorstore.similarity_search(query, k=5)
        context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])

        from config import get_settings
        settings = get_settings()
        llm = init_chat_model(settings.LLM_MODEL)

        prompt = f"""You are analyzing a SEC filing for {ticker.upper()}.

Based on the following excerpts from the filing, answer the analyst's question.
Be specific, cite numbers where available, and stay grounded in the text provided.

FILING EXCERPTS:
{context}

ANALYST QUESTION: {query}

Respond with a JSON object:
{{
  "answer": "detailed answer here",
  "key_points": ["point1", "point2", "point3"],
  "risks_mentioned": ["risk1", "risk2"],
  "sentiment": "Positive" | "Negative" | "Neutral",
  "confidence": 0.0-1.0
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        data = json.loads(content)
        data["ticker"] = ticker.upper()
        data["query"] = query
        data["source"] = "SEC 10-K Filing (RAG)"
        return json.dumps(data)

    except ImportError as e:
        return json.dumps({
            "error": f"RAG dependencies not installed: {e}. Run: pip install faiss-cpu sentence-transformers langchain-huggingface"
        })
    except json.JSONDecodeError:
        return json.dumps({
            "ticker": ticker.upper(),
            "query": query,
            "answer": "Analysis completed but response format was unexpected.",
            "source": "SEC 10-K Filing (RAG)",
        })
    except Exception as e:
        logger.error("RAG pipeline failed: %s", e)
        return json.dumps({"error": f"RAG analysis failed: {e}"})


def _analyze_sec_filing(ticker: str, query: str, form_type: str = "10-K") -> str:
    cik = _get_cik(ticker)
    if not cik:
        return json.dumps({
            "error": f"Could not find SEC CIK for ticker '{ticker}'. Verify the symbol is a US-listed company."
        })

    filing_url = _get_latest_filing_url(cik, form_type)
    if not filing_url:
        return json.dumps({
            "error": f"Could not locate latest {form_type} filing for {ticker} (CIK: {cik})."
        })

    logger.info("Fetching %s filing for %s from %s", form_type, ticker, filing_url)
    raw_text = _fetch_filing_text(filing_url)

    if not raw_text:
        return json.dumps({"error": f"Failed to download filing content from {filing_url}"})

    relevant_text = _extract_relevant_sections(raw_text)
    return _build_rag_response(relevant_text, query, ticker)


sec_filing_rag_tool = StructuredTool(
    name="analyze_sec_filing",
    description=(
        "Fetches a company's latest SEC 10-K or 10-Q filing from EDGAR, "
        "extracts the Risk Factors (Item 1A) and Management Discussion & Analysis (Item 7), "
        "indexes them in a FAISS vector store, and answers analyst queries via RAG. "
        "Use this for qualitative insights: management outlook, competition risks, "
        "regulatory concerns, forward guidance. "
        "Examples: 'What are NVDA main AI competition risks?', "
        "'What does AAPL management say about revenue growth?' "
        "Returns JSON with answer, key points, and sentiment."
    ),
    func=_analyze_sec_filing,
    args_schema=SECFilingInput,
)
