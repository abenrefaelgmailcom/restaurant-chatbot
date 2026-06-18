"""CLI entrypoint for the LangChain + SQLite restaurant chatbot."""

# load_dotenv() reads the .env file and adds its key=value pairs
# to the process environment so os.getenv("OPENAI_API_KEY") works.
from dotenv import load_dotenv

from restaurant_chatbot import RestaurantChatbot
from restaurant_db      import initialize_database


def main() -> None:
    # Load OPENAI_API_KEY (or any other secrets) from the .env file.
    load_dotenv()

    db_path = "restaurant.sqlite"

    # Creates the SQLite file + tables if they don't exist yet,
    # then seeds the demo menu and restaurant info on the very first run.
    initialize_database(db_path)

    # The bot reads the API key from the environment automatically.
    bot = RestaurantChatbot(db_path=db_path)

    print("Restaurant chatbot is ready. Type 'exit' to quit.")
    print("Try: 'What vegetarian dishes do you have?' or 'What are your opening hours?'\n")

    while True:
        # input() blocks until the user presses Enter.
        user_input = input("You: ").strip()

        # Skip empty lines (user just pressed Enter without typing).
        if not user_input:
            continue

        # Graceful exit command.
        if user_input.lower() in {"exit", "quit"}:
            print("Bot: Goodbye!")
            break

        # This single call does classify → fetch DB → generate answer.
        reply = bot.answer(user_input)
        print(f"Bot: {reply}\n")


# Only run main() if this file is executed directly (not imported).
if __name__ == "__main__":
    main()