# Terminal GPT

A terminal-based chat tool for interacting with LLMs via OpenRouter API.

## Features

- **Secure API token storage** - Tokens stored in system keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- Interactive conversation mode with conversation history
- Streaming responses for real-time output
- Multi-line input support (Meta+Enter for newlines)
- Configurable markdown rendering and display options
- First-run setup wizard
- Support for all OpenRouter models

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the setup wizard

The first time you run `ask`, it will automatically launch an interactive setup wizard:

```bash
./ask
```

The wizard will:
1. Prompt for your OpenRouter API token (get one at https://openrouter.ai/keys)
2. Let you choose your preferred model
3. Store your token **securely in your system keychain**
4. Create `~/.askrc` with your preferences

**That's it!** You're ready to chat.

### 3. (Optional) Make the script accessible globally

Create a symlink to use `ask` from anywhere:

```bash
# Linux/macOS
sudo ln -s "$(pwd)/ask" /usr/local/bin/ask

# Or add to your PATH
export PATH="$PATH:$(pwd)"
```

## Usage

### Start a conversation

```bash
# Enter conversation mode
ask

# Start with a question
ask "What is the capital of France?"

# Multi-word questions
ask What is the meaning of life?
```

### In conversation mode

- **Send message**: Type your message and press `Enter`
- **New line**: Press `Shift+Enter` to add a line break
- **Interrupt response**: Press `ESC` to stop the AI response
- **Exit**: Type `bye`, `quit`, or `exit`, or press `Ctrl-C`

## Configuration

### Configuration files

The tool loads configuration in this order:
1. `~/.askrc` (user-level config)
2. `./.askrc` (project-level config, overrides user config)

### Configuration options

- **LLM** (required): The OpenRouter model to use
  - Format: `provider/model`
  - Examples: `anthropic/claude-3.5-haiku`, `openai/gpt-4`, `google/gemini-pro`

- **API_TOKEN** (required): Your OpenRouter API token
  - Can also be set via `ASK_API_TOKEN` environment variable

- **RENDER_MARKDOWN** (optional): Enable markdown rendering
  - Values: `true` or `false`
  - Default: `true`

- **SHOW_PANELS** (optional): Enable/disable surrounding panels/boxes
  - Values: `true` or `false`
  - Default: `true`
  - Set to `false` for a cleaner, minimal output

- **SHOW_COST** (optional): Display token usage and cost after each response
  - Values: `true` or `false`
  - Default: `false`
  - Shows input/output tokens and estimated cost based on model pricing
  - Supports: `anthropic/claude-haiku-4.5`, `openai/gpt-5-mini`, `google/gemini-2.5-flash`

### Environment variable fallback

You can use the `ASK_API_TOKEN` environment variable instead of storing the token in a file:

```bash
export ASK_API_TOKEN=your_token_here
ask "Hello!"
```

## Security

### Secure Token Storage

Terminal GPT stores your OpenRouter API token securely in your system's keychain:

- **macOS**: Keychain Access
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

Your token is **never stored in plain text** in the config file when using the setup wizard.

### Migrating Existing Tokens

If you have an existing `~/.askrc` with a plain text `API_TOKEN`, you'll see a security warning. To migrate to secure storage:

```bash
ask --setup
```

This will:
1. Detect your existing token
2. Offer to migrate it to the system keychain
3. Remove the plain text token from `~/.askrc`
4. Keep all your other settings

### Re-running Setup

You can re-run the setup wizard at any time to:
- Change your API token
- Switch your default model
- Migrate from plain text to keychain storage

```bash
ask --setup
# or
ask -s
```

## Examples

### Basic conversation

```bash
$ ask "Explain quantum computing"
```

### Using different models

Edit your `.askrc` to change the default model:

```bash
# Use GPT-4
LLM=openai/gpt-4

# Use Claude 3.5 Sonnet
LLM=anthropic/claude-3.5-sonnet

# Use Gemini Pro
LLM=google/gemini-pro
```

### Project-specific configuration

Create a `.askrc` in your project directory for project-specific settings:

```bash
cd my-project
echo "LLM=anthropic/claude-haiku-4.5" > .askrc
echo "RENDER_MARKDOWN=false" >> .askrc
chmod 600 .askrc
```

### Cost tracking

Enable cost tracking to monitor your API usage:

```bash
# Add to your ~/.askrc
SHOW_COST=true
```

After each response, you'll see:
```
Tokens: 145 in / 523 out | Cost: $0.0028 ($0.0001 + $0.0026)
```

Pricing (per million tokens):
- **anthropic/claude-haiku-4.5**: $1 input / $5 output
- **openai/gpt-5-mini**: $0.25 input / $2 output
- **google/gemini-2.5-flash**: $0.30 input / $2.50 output

## Security

- Always set `.askrc` permissions to `600` (read/write for user only)
- Never commit `.askrc` files with real API tokens to version control
- Use environment variables for CI/CD environments
- The tool will warn you if your config file has insecure permissions

## Troubleshooting

### "API_TOKEN not specified" error

Make sure you have either:
- Created `~/.askrc` with `API_TOKEN=your_token`
- Set the `ASK_API_TOKEN` environment variable

### "LLM not specified" error

Add the `LLM` setting to your `~/.askrc` file:

```bash
LLM=anthropic/claude-3.5-haiku
```

### "API Error (401)"

Your API token is invalid. Check your OpenRouter account at https://openrouter.ai/keys

### "API Error (429)"

You've hit the rate limit. Wait a moment and try again.

### Markdown rendering issues

Disable markdown rendering in your config:

```bash
RENDER_MARKDOWN=false
```

## How it works

1. **Configuration Loading**: Loads settings from `~/.askrc` and `./.askrc`
2. **Conversation Management**: Maintains chat history using a sliding window (keeps first message + last 20 messages)
3. **API Streaming**: Streams responses from OpenRouter API in real-time
4. **Session Management**: Clears conversation history when you exit

## License

MIT
