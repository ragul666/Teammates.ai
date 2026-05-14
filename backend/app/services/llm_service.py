"""LLM Service — abstracted AI generation with swappable providers.

Architecture Decision:
- Uses a provider pattern so providers can be swapped via env var
- Structured prompt templates for consistent sales follow-up generation
- All AI calls happen server-side only (no API keys in browser)
- Supports: mock (dev), groq (production), openai (alternative)
"""

import asyncio
import random
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_follow_up(
        self,
        lead_name: str,
        company_name: str,
        lead_context: str,
        original_input: str,
    ) -> str:
        """Generate a follow-up email draft."""
        pass


# ─── System prompt used by all real LLM providers ───────────────────────

SALES_SYSTEM_PROMPT = """You are an expert AI sales assistant. Your job is to draft
professional, concise, and compelling follow-up emails for B2B sales outreach.

Guidelines:
- Be professional but warm and personable
- Reference specific context about the lead and their company
- Include 2-3 key value propositions relevant to their situation
- End with a clear, low-pressure call to action
- Keep the email under 200 words
- Start with a compelling subject line in the format: Subject: <your subject>
- Sign off as "AI Sales Assistant"
- Do NOT use markdown formatting — write plain text email"""


class MockLLMProvider(LLMProvider):
    """Mock LLM provider with realistic sales follow-up generation.

    Used for development and testing without consuming API credits.
    """

    TEMPLATES = [
        """Subject: Following up on {company_name}'s {topic}

Hi {lead_name},

I hope this message finds you well. I noticed {observation} and wanted to reach out because I believe we can help {company_name} {value_prop}.

Based on what you shared about {context_ref}, I'd love to show you how our platform can:

• {benefit_1}
• {benefit_2}
• {benefit_3}

Would you be open to a quick 15-minute call this week to explore this further? I'm available Tuesday or Thursday afternoon.

Looking forward to hearing from you.

Best regards,
AI Sales Assistant""",

        """Subject: Quick question about {company_name}'s {topic}

Hi {lead_name},

I came across {observation} and it immediately made me think of how we've helped similar companies in your space.

{context_ref} is exactly the kind of challenge our clients face before working with us. Here's what I think could make a real difference:

1. {benefit_1}
2. {benefit_2}
3. {benefit_3}

I've seen companies like yours achieve {result} within the first quarter of implementation.

Would it make sense to schedule a brief demo? I promise to keep it focused and valuable.

Best,
AI Sales Assistant""",

        """Subject: {lead_name}, a thought on {topic}

Hi {lead_name},

I've been following {company_name}'s recent developments, particularly {observation}. Congratulations on the progress!

Given {context_ref}, I wanted to share how our solution specifically addresses this:

→ {benefit_1}
→ {benefit_2}
→ {benefit_3}

We recently helped a company in a similar situation {result}. I'd be happy to share the case study and discuss how this might apply to {company_name}.

Are you available for a quick chat this week?

Warm regards,
AI Sales Assistant""",
    ]

    TOPICS = [
        "growth strategy", "team expansion", "digital transformation",
        "market expansion", "operational efficiency", "customer engagement",
    ]

    OBSERVATIONS = [
        "your recent product launch", "the team's expansion",
        "your company's growth trajectory", "your recent funding round",
        "your industry leadership position", "your innovative approach",
    ]

    BENEFITS = [
        "Reduce manual follow-up time by 60%",
        "Increase response rates by 3x",
        "Automate lead qualification and scoring",
        "Streamline your sales pipeline management",
        "Get real-time insights on prospect engagement",
        "Personalize outreach at scale",
        "Integrate seamlessly with your existing CRM",
        "Track and optimize conversion metrics",
        "Enable data-driven sales decisions",
    ]

    RESULTS = [
        "increase their conversion rate by 45%",
        "close 30% more deals in Q1",
        "reduce their sales cycle by 2 weeks",
        "double their pipeline velocity",
        "achieve a 4x ROI within 3 months",
    ]

    async def generate_follow_up(
        self,
        lead_name: str,
        company_name: str,
        lead_context: str,
        original_input: str,
    ) -> str:
        """Generate a mock sales follow-up email."""
        # Simulate realistic LLM latency
        await asyncio.sleep(random.uniform(1.0, 2.5))

        template = random.choice(self.TEMPLATES)
        benefits = random.sample(self.BENEFITS, 3)

        # Extract a context reference from the lead context
        context_words = lead_context.split()
        context_ref = " ".join(context_words[:15]) if len(context_words) > 15 else lead_context

        return template.format(
            lead_name=lead_name,
            company_name=company_name,
            topic=random.choice(self.TOPICS),
            observation=random.choice(self.OBSERVATIONS),
            context_ref=context_ref,
            value_prop="streamline your sales operations",
            benefit_1=benefits[0],
            benefit_2=benefits[1],
            benefit_3=benefits[2],
            result=random.choice(self.RESULTS),
        )


class GroqProvider(LLMProvider):
    """Groq LLM provider — fast inference using Groq Cloud.

    Uses the OpenAI-compatible API endpoint that Groq provides.
    """

    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
            self.model = settings.GROQ_MODEL
            logger.info(f"Groq LLM provider initialized (model: {self.model})")
        except ImportError:
            raise RuntimeError("openai package not installed (required for Groq)")

    async def generate_follow_up(
        self,
        lead_name: str,
        company_name: str,
        lead_context: str,
        original_input: str,
    ) -> str:
        """Generate a follow-up email using Groq."""
        user_prompt = f"""Generate a follow-up email for this sales lead:

Lead Name: {lead_name}
Company: {company_name}
Lead Context: {lead_context}
Original Signal/Message: {original_input}

Draft a professional follow-up email including a subject line."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SALES_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """Real OpenAI provider for production use."""

    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        except ImportError:
            raise RuntimeError("openai package not installed")

    async def generate_follow_up(
        self,
        lead_name: str,
        company_name: str,
        lead_context: str,
        original_input: str,
    ) -> str:
        """Generate a follow-up email using OpenAI."""
        user_prompt = f"""Generate a follow-up email for this sales lead:

Lead Name: {lead_name}
Company: {company_name}
Lead Context: {lead_context}
Original Signal/Message: {original_input}

Draft a professional follow-up email including a subject line."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SALES_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider.

    Priority: groq > openai > mock
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq" and settings.GROQ_API_KEY:
        return GroqProvider()
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    else:
        if provider not in ("mock", ""):
            logger.warning(
                f"LLM_PROVIDER='{provider}' but API key is missing. "
                "Falling back to mock provider."
            )
        return MockLLMProvider()
