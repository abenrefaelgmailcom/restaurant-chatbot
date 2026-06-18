# Restaurant Chatbot

AI-powered restaurant assistant built with:

* Python
* SQLite
* LangChain
* OpenAI
* Gradio

## Features

* Menu search
* Vegetarian dishes
* Desserts
* Drinks
* Spicy dishes
* Opening hours
* Modern Gradio interface

## Installation

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

Run terminal version:

```bash
python restaurant_chatbot_app.py
```

Run Gradio version:

```bash
python restaurant_chatbot_gradio.py
```
