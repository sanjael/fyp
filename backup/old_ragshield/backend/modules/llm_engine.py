"""
LLM Engine Module
=================
Handles response generation using Google Gemini API (google-genai SDK).
Enforces context-grounded answering with strict system prompts.
"""

from typing import List, Dict, Optional

import config

# System prompt that enforces context-only answering
RAGSHIELD_SYSTEM_PROMPT = """You are RAGShield Assistant, a highly accurate and trustworthy AI assistant.

CRITICAL INSTRUCTIONS:
1. Answer ONLY using the provided context. Do NOT use any prior knowledge.
2. If the answer is NOT found in the context, respond: "I don't have sufficient evidence in the provided documents to answer this question accurately."
3. Be precise, concise, and factual.
4. When possible, indicate WHICH source your answer comes from.
5. Do NOT hallucinate, speculate, or guess.
6. If context contains contradictions, acknowledge them: "Sources differ on this topic..."

Your goal is to provide reliable, grounded answers that users can trust."""

VERIFICATION_SYSTEM_PROMPT = """You are RAGShield Assistant operating in VERIFICATION MODE due to high hallucination risk.

STRICT INSTRUCTIONS:
1. Answer ONLY from the verified context below.
2. Cross-reference claims across multiple provided sources.
3. If sources conflict, list the conflicting claims and indicate uncertainty.
4. Confidence level must be stated at the end: [Confidence: Low/Medium/High]
5. If insufficient evidence exists, say: "Insufficient verified evidence for a reliable answer."
6. Never fabricate citations or facts."""


class LLMEngine:
    """
    LLM engine for RAGShield.
    Supports OpenRouter (via openai SDK) and Google Gemini API (via google.genai).
    Generates grounded, context-faithful responses.
    """

    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env file.")

        self._sdk = "unknown"
        self._openai_client = None
        self._genai_client = None
        self._old_model = None

        if config.GEMINI_API_KEY.startswith("sk-or-"):
            # Use OpenRouter via OpenAI SDK
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=config.GEMINI_API_KEY,
                )
                self._sdk = "openrouter"
            except ImportError:
                raise ImportError("openai package is required for OpenRouter keys. Run: pip install openai")
        else:
            # Use Google GenAI
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
                self._sdk = "new_gemini"
            except (ImportError, Exception):
                # Fallback to old SDK
                try:
                    import google.generativeai as genai_old
                    genai_old.configure(api_key=config.GEMINI_API_KEY)
                    self._old_model = genai_old.GenerativeModel(config.LLM_MODEL)
                    self._sdk = "old_gemini"
                except ImportError:
                    raise ImportError("Neither google-genai nor google-generativeai is installed.")

        print(f"[LLMEngine] Initialized with model: {config.LLM_MODEL} (SDK: {self._sdk})")

    def generate(
        self,
        query: str,
        context_chunks: List[Dict],
        risk_level: str = "low",
        strategy: str = "direct_generation",
    ) -> Dict:
        """
        Generate a grounded response from the query and context chunks.
        """
        if not context_chunks:
            return self._no_context_response(query)

        context_str = self._build_context_string(context_chunks)
        system_prompt = (
            VERIFICATION_SYSTEM_PROMPT if risk_level == "high" else RAGSHIELD_SYSTEM_PROMPT
        )
        prompt = self._build_prompt(query, context_str, system_prompt, risk_level)

        try:
            if self._sdk == "openrouter":
                answer_text = self._generate_openrouter(system_prompt, prompt)
            elif self._sdk == "new_gemini":
                answer_text = self._generate_new_sdk(prompt)
            else:
                answer_text = self._generate_old_sdk(prompt)

            sources = self._extract_sources(context_chunks)
            confidence = self._estimate_confidence(risk_level, context_chunks)

            return {
                "answer": answer_text,
                "sources": sources,
                "confidence": confidence,
                "strategy": strategy,
                "risk_level": risk_level,
                "context_used": len(context_chunks),
                "model": config.LLM_MODEL,
                "error": None,
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[LLMEngine] Generation error: {error_msg}")
            return {
                "answer": f"Generation failed: {error_msg}",
                "sources": [],
                "confidence": "low",
                "strategy": strategy,
                "risk_level": risk_level,
                "context_used": 0,
                "model": config.LLM_MODEL,
                "error": error_msg,
            }

    def _generate_openrouter(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using OpenRouter (via OpenAI SDK)."""
        response = self._openai_client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

    def _generate_new_sdk(self, prompt: str) -> str:
        """Generate using the new google.genai SDK."""
        from google.genai import types
        response = self._genai_client.models.generate_content(
            model=config.LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=config.LLM_TEMPERATURE,
                max_output_tokens=config.LLM_MAX_TOKENS,
            ),
        )
        return response.text.strip()

    def _generate_old_sdk(self, prompt: str) -> str:
        """Generate using the legacy google.generativeai SDK."""
        import google.generativeai as genai
        response = self._old_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=config.LLM_TEMPERATURE,
                max_output_tokens=config.LLM_MAX_TOKENS,
            ),
        )
        return response.text.strip()

    def _build_context_string(self, chunks: List[Dict]) -> str:
        """Build formatted context string from chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "Unknown")
            year = chunk.get("year", "")
            cqs = chunk.get("cqs_score", "")
            text = chunk.get("text", "")

            part = f"[Source {i}: {source} ({year})"
            if cqs:
                part += f" | Quality: {cqs:.0f}/100"
            part += f"]\n{text}"
            context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str, system_prompt: str, risk_level: str) -> str:
        """Construct the full prompt."""
        risk_note = ""
        if risk_level == "medium":
            risk_note = "\nNote: Context quality is moderate. Answer carefully."
        elif risk_level == "high":
            risk_note = "\nHIGH RISK MODE: Extra caution required. Cross-verify all claims."

        return f"""{system_prompt}
{risk_note}

=== VERIFIED CONTEXT ===
{context}

=== QUESTION ===
{query}

=== YOUR ANSWER ==="""

    def _no_context_response(self, query: str) -> Dict:
        """Response when no context passed the shield."""
        return {
            "answer": (
                "RAGShield blocked all retrieved documents due to insufficient quality. "
                "No reliable context is available to answer this question. "
                "Please try uploading more relevant documents or refine your query."
            ),
            "sources": [],
            "confidence": "none",
            "strategy": "blocked",
            "risk_level": "high",
            "context_used": 0,
            "model": config.LLM_MODEL,
            "error": None,
        }

    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique sources from context chunks."""
        seen = set()
        sources = []
        for chunk in chunks:
            source = chunk.get("source", "unknown")
            if source not in seen:
                seen.add(source)
                sources.append({
                    "filename": source,
                    "title": chunk.get("title", source),
                    "year": chunk.get("year", "Unknown"),
                    "source_type": chunk.get("source_type", "unknown"),
                    "cqs_score": chunk.get("cqs_score", None),
                })
        return sources

    def _estimate_confidence(self, risk_level: str, chunks: List[Dict]) -> str:
        """Estimate answer confidence based on risk level and context quality."""
        avg_cqs = (
            sum(c.get("cqs_score", 50) for c in chunks) / len(chunks)
            if chunks else 0
        )
        if risk_level == "low" and avg_cqs >= 75:
            return "high"
        elif risk_level == "medium" or (risk_level == "low" and avg_cqs >= 60):
            return "medium"
        else:
            return "low"
