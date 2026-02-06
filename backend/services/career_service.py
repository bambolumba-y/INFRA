"""Career service — PDF resume parsing and job matching."""

from __future__ import annotations

import io
import json
import logging

import pymupdf  # type: ignore[import-untyped]

from backend.llm.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = (
    "You are an expert recruiter AI. Given the raw text of a resume, "
    "extract structured data as JSON with the keys: "
    '"name", "skills" (list of strings), "experience_years" (int), '
    '"stack" (list of strings), "summary" (short paragraph). '
    "Respond ONLY with the JSON object."
)

MATCH_PROMPT = (
    "You are a career-matching AI. Given a candidate profile (JSON) and "
    "a job description, return a JSON object with: "
    '"match_percentage" (0-100), "matching_skills" (list), '
    '"missing_skills" (list), "recommendation" (short paragraph). '
    "Respond ONLY with the JSON object."
)


async def parse_resume_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF resume using PyMuPDF."""
    doc = pymupdf.open(stream=io.BytesIO(file_bytes), filetype="pdf")
    text_parts: list[str] = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


async def extract_resume_data(text: str) -> dict:
    """Use LLM to extract structured data from resume text."""
    llm = ProviderFactory()
    messages = [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": text[:6000]},
    ]
    response = await llm.completion(messages=messages)
    try:
        return json.loads(response.content)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM resume extraction: %s", response.content)
        return {"raw_text": text[:2000]}


async def match_resume_to_job(resume_data: dict, job_description: str) -> dict:
    """Score how well a resume matches a job description using LLM."""
    llm = ProviderFactory()
    messages = [
        {"role": "system", "content": MATCH_PROMPT},
        {
            "role": "user",
            "content": (
                f"Candidate profile:\n{json.dumps(resume_data, indent=2)}\n\n"
                f"Job description:\n{job_description}"
            ),
        },
    ]
    response = await llm.completion(messages=messages)
    try:
        return json.loads(response.content)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM match response: %s", response.content)
        return {"match_percentage": 0, "recommendation": "Unable to compute match"}
