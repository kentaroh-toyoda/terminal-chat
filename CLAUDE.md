- Make a command that I can ask an LLM in the terminal. Usage: `ask ...`
- a configuration file has to be read (a dot file) to load a model (via OpenRouter)
and an API token.
LLM=anthropic/claude-haiku-4.5
API_TOKEN=...
- When ask something, it should enter a conversation mode like a chat bot. During the session, past conversations have to be memoried.
- type "bye", "quit", "exit" (case insensitive), or Ctrl-C to quit.
- Hence the outputs should be terminal-frinedly with text decoratons (bold, italic, underline, colors).