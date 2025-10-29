# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-29

### Added
- Initial beta release
- Terminal-based chat interface with LLMs via OpenRouter API
- Interactive conversation mode with history management
- Sliding window conversation management (configurable message limit)
- Multiple LLM support (Claude, GPT, Gemini via OpenRouter)
- Secure API token storage using system keychain
- Configuration file support (`.askrc`)
- Rich terminal formatting with markdown rendering
- Real-time cost tracking for API usage
- Four guardrail modes for content safety:
  - System-level guardrails
  - External guardrails (Llama Guard 4)
  - Intent-based guardrails
  - No guardrails (for trusted use)
- User-friendly Llama Guard 4 category messages (S1-S14)
- Keyboard interrupt support (ESC key) during streaming
- Setup wizard for easy configuration
- Comprehensive test suite (73% pass rate, 156/214 tests passing)

### Features
- Command: `ask` - Start interactive chat session
- Commands during session:
  - `/cost` - Show token usage and cost
  - `/clear` - Clear conversation history
  - `/config` - Show current configuration
  - `bye`, `quit`, `exit`, or Ctrl-C to exit
- Configuration options:
  - Model selection
  - Token management (keychain, environment, file)
  - Guardrail configuration
  - Display options (markdown, panels, intent info)
  - Conversation limits

### Known Issues
- Some advanced guardrail tests failing (intent parsing edge cases)
- Integration test suite has some failures (mocking infrastructure)
- Code coverage at 13% (focused on core functionality)

### Notes
- This is a beta release - expect some rough edges
- Report issues at: https://github.com/kentaroh_toyoda/terminal-chat/issues
- Core functionality (chat, config, cost tracking) is stable and well-tested

[0.1.0]: https://github.com/kentaroh_toyoda/terminal-chat/releases/tag/v0.1.0
