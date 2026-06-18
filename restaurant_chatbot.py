"""LangChain chatbot that routes questions to menu/details/other."""

import os
from typing import List
from dotenv import load_dotenv

# StrOutputParser converts the LLM's response object into a plain Python string.
from langchain_core.output_parsers import StrOutputParser
# ChatPromptTemplate builds the messages list we send to the LLM.
from langchain_core.prompts import ChatPromptTemplate
# ChatOpenAI is the LangChain wrapper around the OpenAI chat models.
from langchain_openai import ChatOpenAI

from restaurant_db import get_restaurant_details_and_hours, search_menu_items


class RestaurantChatbot:
    """RAG-style restaurant assistant backed by SQLite tables."""

    def __init__(self, db_path: str, model_name: str = "gpt-4o-mini") -> None:
        self.db_path = db_path
        self.llm = None  # start as None — only set if we have an API key

        # Load variables from .env.
        # override=True makes sure the .env key replaces an old Windows environment key.
        load_dotenv(override=True)

        # os.getenv returns None if the variable is missing — safe to call always.
        if os.getenv("OPENAI_API_KEY"):
            # temperature=0 → deterministic answers (no random creativity).
            # Great for factual tasks like restaurant Q&A.
            self.llm = ChatOpenAI(model=model_name, temperature=0)

        # ── CLASSIFIER PROMPT ────────────────────────────────────────────
        # This prompt instructs the LLM to return exactly one word:
        # "menu", "details", or "other". The | pipe syntax chains the
        # prompt → LLM → parser together into a reusable "chain".
        self.classifier_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a router. Classify each question as exactly one label: "
                    "menu, details, or other. Return only the label.",
                ),
                ("human", "Question: {question}"),
            ]
        )

        # ── ANSWER PROMPT ────────────────────────────────────────────────
        # The {context} placeholder will be filled with the SQLite rows we
        # retrieved. Grounding the LLM in real data prevents hallucination.
        self.answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful restaurant assistant. Use only the provided context. "
                    "If context does not contain the answer, say you are not sure and ask a clarifying question. "
                    "Never ask which restaurant the user means.",
                ),
                ("human", "Question: {question}\n\nContext:\n{context}"),
            ]
        )

    def classify_question(self, question: str) -> str:
        """Classify into menu/details/other — keyword matching first, LLM as fallback."""
        lower_q = question.lower()

        # ── FAST KEYWORD FALLBACK ────────────────────────────────────────
        # Before calling the LLM (which costs money and takes time),
        # check if the question contains obvious menu or details keywords.
        # This means the chatbot routes correctly even with no API key.
        if any(k in lower_q for k in [
            "menu", "dish", "dishes", "food", "price",
            "vegan", "vegetarian", "spicy",
            "drink", "drinks", "beverage", "beverages",
            "dessert", "desserts", "sweet", "sweets",
            "starter", "starters", "appetizer", "appetizers",
            "main", "mains", "meal", "meals",
            "option", "options", "serve", "serving",
            "eat", "order", "available",
            "cheap", "cheapest",
        ]):
            return "menu"

        if any(k in lower_q for k in [
            "hour", "hours", "open", "close", "address",
            "phone", "location", "email", "website",
        ]):
            return "details"

        # No keyword matched and no LLM available — default to "other".
        if not self.llm:
            return "other"

        # ── LLM CLASSIFICATION ───────────────────────────────────────────
        # Build the chain: prompt → LLM → string parser, then invoke it.
        chain = self.classifier_prompt | self.llm | StrOutputParser()
        label = chain.invoke({"question": question}).strip().lower()

        # Guard against unexpected LLM output (safety net).
        if label in {"menu", "details", "other"}:
            return label
        return "other"

    def _extract_menu_search_text(self, question: str) -> str:
        """Convert natural-language menu questions into cleaner DB search terms."""
        lower_q = question.lower()

        # The database search function works better with short keywords
        # than with full natural-language questions.

        # Natural vegetarian questions:
        # "Do you have vegetarian food?"
        # "Any vegan options?"
        if (
            "vegetarian" in lower_q
            or "vegan" in lower_q
            or "meat free" in lower_q
            or "without meat" in lower_q
        ):
            return "vegetarian"

        # Natural dessert questions:
        # "Show me desserts"
        # "Do you have something sweet?"
        if (
            "dessert" in lower_q
            or "desserts" in lower_q
            or "sweet" in lower_q
            or "sweets" in lower_q
        ):
            return "dessert"

        # Natural starter questions:
        # "Any appetizers?"
        # "What can I start with?"
        if (
            "starter" in lower_q
            or "starters" in lower_q
            or "appetizer" in lower_q
            or "appetizers" in lower_q
            or "start with" in lower_q
        ):
            return "starter"

        # Natural main-course questions:
        # "What meals do you serve?"
        # "What main courses are available?"
        if (
            "main" in lower_q
            or "mains" in lower_q
            or "main course" in lower_q
            or "main courses" in lower_q
            or "meal" in lower_q
            or "meals" in lower_q
        ):
            return "main"

        # Natural drink questions:
        # "What can I drink?"
        # "Any beverages?"
        if (
            "drink" in lower_q
            or "drinks" in lower_q
            or "beverage" in lower_q
            or "beverages" in lower_q
            or "what can i drink" in lower_q
        ):
            return "drink"

        # Natural spicy questions:
        # "Any spicy options?"
        # "Do you have hot food?"
        if (
            "spicy" in lower_q
            or "hot food" in lower_q
            or "hot dish" in lower_q
            or "hot dishes" in lower_q
        ):
            return "spicy"

        # If no known filter/category is found, fall back to the original question.
        return question

    def _build_menu_context(self, question: str) -> tuple[str, bool]:
        # Search the database for items matching the question's keywords.
        # Instead of passing the full user question, extract a cleaner search term first.
        search_text = self._extract_menu_search_text(question)
        rows = search_menu_items(self.db_path, search_text)

        if not rows:
            return "No menu records matched the question.", False

        lines: List[str] = []
        for row in rows:
            # Convert SQLite integers (0/1) to human-readable labels.
            veg = "vegetarian" if row["is_vegetarian"] else "non-vegetarian"
            spicy = "spicy" if row["is_spicy"] else "not spicy"
            status = "available" if row["is_available"] else "currently unavailable"

            lines.append(
                f"- {row['item_name']} ({row['category']}): {row['description']} | "
                f"${row['price']:.2f} | {veg}, {spicy}, {status}"
            )

        return "\n".join(lines), True

    def _build_details_context(self) -> str:
        details, hours = get_restaurant_details_and_hours(self.db_path)
        if not details:
            return "No restaurant details found."

        # Format the single restaurant row as readable key-value text.
        details_text = (
            f"Name: {details['name']}\n"
            f"Address: {details['address']}\n"
            f"Phone: {details['phone']}\n"
            f"Email: {details['email']}\n"
            f"Website: {details['website']}"
        )

        # Build one line per weekday, appending any notes in parentheses.
        hours_lines = [
            f"- {h['day_of_week']}: {h['open_time']} to {h['close_time']}"
            + (f" ({h['notes']})" if h.get("notes") else "")
            for h in hours
        ]
        return details_text + "\n\nOpening Hours:\n" + "\n".join(hours_lines)

    def answer(self, question: str) -> str:
        """Route question, retrieve matching SQLite data, and generate an answer."""
        # Step 1: find out which data source we need.
        route = self.classify_question(question)

        # Step 2: fetch the relevant rows from the database.
        if route == "menu":
            context, has_match = self._build_menu_context(question)
            if not has_match:
                return (
                    "I could not find that item in the current menu. "
                    "Ask me to list available mains, starters, desserts, or drinks."
                )
        elif route == "details":
            context = self._build_details_context()
        else:
            # Off-topic — no database access needed, return a polite refusal.
            return (
                "I can help with menu items, prices, ingredients, and restaurant details "
                "like opening hours, phone, and address."
            )

        # Step 3: if no LLM, return the raw context directly (free fallback mode).
        if not self.llm:
            return f"(Local fallback, no OpenAI key configured)\n{context}"

        # Step 4: hand the context to the LLM and let it write a friendly answer.
        chain = self.answer_prompt | self.llm | StrOutputParser()
        return chain.invoke({"question": question, "context": context})