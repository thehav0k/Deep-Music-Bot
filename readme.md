# Music Bot

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.x-lightgrey.svg)](https://discordpy.readthedocs.io/)

A Discord music and AI chatbot built with Python. Play music from YouTube, manage queues and playlists, and chat with AI using the DeepSeek API directly in your server.

## Features

- 🎵 Play audio from YouTube links or search queries
- ⏭️ Queue songs or play next
- ⏸️ Pause, resume, and stop playback
- 🔁 Loop current track
- 📜 Create and manage playlists
- 🔊 Auto-disconnect after inactivity
- 🤖 AI chat using the DeepSeek API with memory and intent handling
- 🎶 Fetch lyrics via AI
- 💬 Natural-language commands in chat (no slash prefix needed)

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed and in your PATH
- Opus library (`libopus`) for voice support

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/Deep-Music-Bot.git
   cd Deep-Music-Bot
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Discord bot token
BOT_TOKEN=your_discord_bot_token

# DeepSeek AI API key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

> **Note:** On macOS with Homebrew, you may need to load Opus manually. If the bot fails to find `libopus`, install it via:
> ```bash
> brew install opus
> ```

## Usage

Run the bot:

```bash
python main.py
```

Once connected, use slash commands or natural language messages in Discord channels where the bot is present.

## Commands

| Command               | Description                                               |
|-----------------------|-----------------------------------------------------------|
| `/play <query>`       | Play a song from YouTube or search query                  |
| `/next <query>`       | Add a song to the queue                                   |
| `/stop`               | Pause the current track                                   |
| `/resume`             | Resume paused playback                                    |
| `/exit`               | Stop playback and disconnect from voice channel           |
| `/loop`               | Toggle looping of the current track                       |
| `/list <name> <query>`| Add a song to a named playlist                           |
| `/ask <question>`     | Chat with AI, supports play & recommend intents           |
| `/forget`             | Clear AI chat memory for the channel                      |
| `/over`               | End AI chat session                                       |
| `/lyrics <song>`      | Fetch lyrics via AI                                       |

Natural-language messages without prefix also work when a chat session is active.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/YourFeature`)
3. Make your changes and test
4. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [DeepSeek API](https://openrouter.ai/)

