"""Modern Gradio UI for the Restaurant Chatbot."""

import gradio as gr

from restaurant_chatbot import RestaurantChatbot

# Create chatbot instance once when the application starts.
bot = RestaurantChatbot("restaurant.sqlite")


def respond(message, history):
    """Send user message to chatbot and return response."""
    if not message.strip():
        return "", history

    bot_reply = bot.answer(message)

    # Gradio Chatbot in your version expects a list of tuples:
    # [(user_message, bot_reply), ...]
    history.append(
        (
            message,
            bot_reply,
        )
    )

    return "", history


custom_css = """
body {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 50%, #fef3c7 100%);
}

.main-header {
    text-align: center;
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white;
    margin-bottom: 20px;
}

.main-header h1 {
    margin: 0;
    font-size: 40px;
}

.main-header p {
    margin-top: 10px;
    font-size: 18px;
}

.info-card {
    background: white;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.footer {
    text-align: center;
    margin-top: 15px;
    color: #7c2d12;
}
"""


with gr.Blocks(
    title="Sunset Bistro AI Assistant",
    theme=gr.themes.Soft(
        primary_hue="orange",
        secondary_hue="amber",
    ),
    css=custom_css,
) as demo:

    gr.HTML(
        """
        <div class="main-header">
            <h1>🍽️ Sunset Bistro</h1>
            <p>AI Restaurant Assistant</p>
        </div>
        """
    )

    with gr.Row():

        with gr.Column(scale=1):

            gr.HTML(
                """
                <div class="info-card">
                    <h3>🔥 Popular Dishes</h3>
                    <p>🍕 Margherita Pizza</p>
                    <p>🍄 Mushroom Risotto</p>
                    <p>🍔 Spicy Chicken Burger</p>
                </div>
                """
            )

            gr.HTML(
                """
                <div class="info-card">
                    <h3>💬 Ask Me About</h3>
                    <p>🌱 Vegetarian dishes</p>
                    <p>🍰 Desserts</p>
                    <p>☕ Drinks</p>
                    <p>🌶️ Spicy options</p>
                    <p>🕒 Opening hours</p>
                </div>
                """
            )

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Restaurant Chat",
                height=550,
            )

            message = gr.Textbox(
                label="Your Question",
                placeholder="What vegetarian dishes do you have?",
            )

            with gr.Row():
                send_btn = gr.Button(
                    "Send 🚀",
                    variant="primary",
                )

                clear_btn = gr.ClearButton(
                    [message, chatbot]
                )

            gr.Examples(
                examples=[
                    ["What vegetarian dishes do you have?"],
                    ["Show me desserts"],
                    ["What drinks do you have?"],
                    ["Any spicy options?"],
                    ["What are your opening hours?"],
                ],
                inputs=message,
            )

    gr.HTML(
        """
        <div class="footer">
            Built with Python • SQLite • LangChain • OpenAI • Gradio
        </div>
        """
    )

    send_btn.click(
        respond,
        inputs=[message, chatbot],
        outputs=[message, chatbot],
    )

    message.submit(
        respond,
        inputs=[message, chatbot],
        outputs=[message, chatbot],
    )


if __name__ == "__main__":
    demo.launch()