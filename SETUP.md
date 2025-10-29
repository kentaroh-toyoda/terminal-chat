# Quick Setup Guide

## Prerequisites

- Python 3.7 or higher
- OpenRouter API account (https://openrouter.ai)

## Installation Steps

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the interactive setup wizard

Simply run `ask` for the first time, and it will automatically start the setup wizard:

```bash
./ask
```

The wizard will:
1. **Prompt for your OpenRouter API token** (with masked input for security)
2. **Let you choose your preferred model** from popular options
3. **Store your token securely** in your system keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
4. **Create `~/.askrc`** with your non-sensitive preferences

### 3. Start chatting!

```bash
./ask "Hello, who are you?"
```

### 4. (Optional) Make it globally accessible

**Option A: Symlink**
```bash
sudo ln -s "$(pwd)/ask" /usr/local/bin/ask
```

**Option B: Add to PATH**

Add this to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$PATH:/Users/kentaroh_toyoda/projects/terminal-chat"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Verify Installation

```bash
# Should work from any directory
ask "What is 2+2?"
```

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Try different models by changing the `LLM` setting
- Create project-specific `.askrc` files for different use cases
