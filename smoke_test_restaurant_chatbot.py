"""Smoke test for the SQLite-backed restaurant chatbot."""

import os
import tempfile
import uuid

from restaurant_chatbot import RestaurantChatbot
from restaurant_db      import get_menu_items, get_restaurant_details_and_hours, initialize_database


def run_smoke_test() -> None:
    # Use a unique temp file so the test never pollutes the real database.
    # uuid.uuid4().hex gives a random 32-character hex string.
    db_path = os.path.join(tempfile.gettempdir(), f"test_restaurant_{uuid.uuid4().hex}.sqlite")
    initialize_database(db_path)

    # ── VERIFY DATABASE CONTENTS ─────────────────────────────────────
    menu             = get_menu_items(db_path)
    details, hours   = get_restaurant_details_and_hours(db_path)

    # assert raises AssertionError and prints the message if the condition is False.
    assert len(menu) >= 3,         "Menu should have seeded items"
    assert details.get("name"),     "Restaurant details should be seeded"
    assert len(hours) == 7,         "Opening hours should include all days"

    # ── FORCE OFFLINE MODE ───────────────────────────────────────────
    # Temporarily remove the API key from the environment.
    # This tests that keyword routing + fallback answers work with no OpenAI access.
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        bot = RestaurantChatbot(db_path=db_path)

        # Should route to "menu" via keyword "vegetarian".
        menu_reply         = bot.answer("What vegetarian dishes are on the menu?")
        # "fish" is not in the seed data → no match reply.
        missing_item_reply = bot.answer("Do you have fish in the menu?")
        # Should route to "details" via keywords "hours" and "address".
        details_reply      = bot.answer("What are your opening hours and address?")
        # Off-topic question → polite refusal.
        other_reply        = bot.answer("Can you tell me a joke?")
    finally:
        # Always restore the key so other tests in the same session still work.
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key

    # ── ASSERTIONS ───────────────────────────────────────────────────
    assert "Margherita Pizza"      in menu_reply or "Mushroom Risotto" in menu_reply
    assert "could not find that item" in missing_item_reply
    assert "Opening Hours"           in details_reply and "Address" in details_reply
    assert "I can help with menu items" in other_reply

    # Best-effort cleanup — on Windows the file may still be locked.
    try:
        os.remove(db_path)
    except OSError:
        pass


if __name__ == "__main__":
    run_smoke_test()
    print("smoke_test_restaurant_chatbot.py: PASS")