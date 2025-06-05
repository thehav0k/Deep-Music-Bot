import requests
import os

def send_message(history):
    """Send the chat history to DeepSeek API and return the assistant's reply."""
    API_KEY = os.getenv('DEEPSEEK_API_KEY') or 'Your api key'
    API_URL = 'https://openrouter.ai/api/v1/chat/completions'
    HEADERS = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": "deepseek/deepseek-chat:free",
        "messages": history
    }
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        print("Bot: [Network Error]", e)
    except (ValueError, KeyError, IndexError):
        print("Bot: [Error] Unexpected response format.")
        try:
            print("Raw Response:", response.text)
        except:
            pass
    return None


def main():
    print("💬 DeepSeek Chatbot (type 'exit' to quit)")
    chat_history = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {'exit', 'quit'}:
            print("👋 Exiting chat. Goodbye!")
            break
        chat_history.append({"role": "user", "content": user_input})
        reply = send_message(chat_history)
        if reply:
            print("Bot:", reply)
            chat_history.append({"role": "assistant", "content": reply})


if __name__ == '__main__':
    main()

