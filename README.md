# Ask: Terminal GPT

A terminal-based chat tool for interacting with LLMs via OpenRouter API.

## ⚠️ Beta Status

**This is a beta release (v0.1.0)** - The core functionality is stable and well-tested, but some advanced features are still being refined.

- **Stable Features**: Chat interface, configuration, cost tracking, basic guardrails
- **Bug Reports**: Please report issues at [GitHub Issues](https://github.com/kentaroh_toyoda/terminal-chat/issues)

## Features

- Interactive conversation mode with conversation history
- Streaming responses with markdown rendering
- Secure API token storage in system keychain
- Customizable guardrails for content safety
- Token usage and cost tracking
- Support for all OpenRouter models

## Installation

```bash
# From PyPI (when published)
pip install terminal-chat

# From source
pip install .

# Development mode
pip install -e .
```

## Quick Start

Run `ask` for the first time to launch the setup wizard:

```bash
ask
```

The wizard will:
1. Prompt for your OpenRouter API token (get one at https://openrouter.ai/keys)
2. Let you choose your preferred model
3. Store your token securely in your system keychain
4. Create `~/.askrc` with your preferences

**That's it!** You're ready to chat.

## Usage

```bash
# Enter conversation mode
ask

# Start with a question
ask "What is the capital of France?"
```

### In conversation mode

- **Send message**: Type and press `Enter`
- **New line**: Press `Shift+Enter`
- **Interrupt response**: Press `ESC`
- **Exit**: Type `bye`, `quit`, `exit`, or press `Ctrl-C`

## Configuration

Configuration files are loaded in order:
1. `~/.askrc` (user-level)
2. `./.askrc` (project-level, overrides user config)

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| **Required** |||
| `LLM` | *(required)* | Model to use (format: `provider/model`) |
| `API_TOKEN` | *(set via `ask --setup`)* | OpenRouter API token (stored in keychain) |
| **Display** |||
| `RENDER_MARKDOWN` | `true` | Enable markdown formatting |
| `SHOW_PANELS` | `true` | Show bordered panels around responses |
| `SHOW_COST` | `false` | Display token usage and cost after each response |
| `INPUT_PREFIX` | `"> "` | Customize prompt prefix |
| **API Limits** |||
| `MAX_TOKENS` | `4096` | Maximum tokens per API request |
| `MAX_INPUT_LENGTH` | `10000` | Maximum characters in user input |
| **Guardrails** |||
| `GUARDRAIL` | `system` | Mode: `system`, `external`, `intent`, or `none` |
| `EXTERNAL_GUARDRAIL_MODEL` | `meta-llama/llama-guard-4-12b` | Model for external guardrails |
| `EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS` | `both` | When to check: `input`, `output`, or `both` |
| `SHOW_INTENT` | `true` | Show intent analysis (for `intent` mode) |
| **Advanced** |||
| `SYSTEM_PROMPT` | *(default safety prompt)* | Custom system prompt for the LLM |

### Example .askrc

```bash
# Required
LLM=anthropic/claude-haiku-4.5
# API_TOKEN stored in keychain (run: ask --setup)

# Display
RENDER_MARKDOWN=true
SHOW_PANELS=true
SHOW_COST=false
INPUT_PREFIX=>

# API Limits
MAX_TOKENS=4096
MAX_INPUT_LENGTH=10000

# Guardrails
GUARDRAIL=system
EXTERNAL_GUARDRAIL_MODEL=meta-llama/llama-guard-4-12b  # For GUARDRAIL=external
EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS=both  # For GUARDRAIL=external
SHOW_INTENT=true  # For GUARDRAIL=intent

# Advanced
# SYSTEM_PROMPT=You are a helpful AI assistant.
```

## Guardrails

Terminal Chat provides four content safety modes:

### `system` (Default)
Uses system prompts to guide safe LLM behavior. Fast, no extra API calls, works with all models.

```bash
GUARDRAIL=system
```

### `external`
Uses Llama Guard 4 as an independent content filter. Checks input/output against 14 safety categories (Violent Crimes, Non-Violent Crimes, Sex-Related Crimes, Child Exploitation, Defamation, Specialized Advice, Privacy, IP Violations, Indiscriminate Weapons, Hate Speech, Self-Harm, Sexual Content, Elections, Code Interpreter Abuse).

```bash
GUARDRAIL=external
EXTERNAL_GUARDRAIL_MODEL=meta-llama/llama-guard-4-12b
EXTERNAL_GUARDRAIL_CHECK_DIRECTIONS=both  # input, output, or both
```

**Blocked message example:**
```
❌ Input blocked by guardrail: Indiscriminate Weapons (S9)
Please rephrase your message to avoid this content.
```

### `intent`
LLM analyzes request intent and appropriateness before responding. Context-aware but adds overhead.

```bash
GUARDRAIL=intent
SHOW_INTENT=true
```

### `none`
Disables all guardrails. ⚠️ Use with caution in trusted environments only.

```bash
GUARDRAIL=none
```

## Security

### Token Storage

Your API token is stored securely in your system keychain:
- **macOS**: Keychain Access
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

Run `ask --setup` to store or migrate your token. Tokens are never stored in plain text in config files.

### Cost Tracking

Enable cost monitoring with `SHOW_COST=true`:

```
Tokens: 145 in / 523 out | Cost: $0.0028 ($0.0001 + $0.0026)
```

**Pricing (per million tokens):**
- **anthropic/claude-haiku-4.5**: $1 input / $5 output
- **openai/gpt-5-mini**: $0.25 input / $2 output
- **google/gemini-2.5-flash**: $0.30 input / $2.50 output

## Development

```bash
git clone https://github.com/kentaroh_toyoda/terminal-chat.git
cd terminal-chat
pip install -e .  # Editable install for development
```

## Support

If you find this project helpful, consider supporting development:

**USDC (Ethereum)**: [0xDf6B7a400bCA18c30876e843B96f218A5Ed1c5BC](ethereum:0xDf6B7a400bCA18c30876e843B96f218A5Ed1c5BC) ([View on Etherscan](https://etherscan.io/address/0xDf6B7a400bCA18c30876e843B96f218A5Ed1c5BC))

## License

MIT
