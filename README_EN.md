# DeepPhase

English | [简体中文](README.md)

An intelligent Phase executor based on Claude Agent SDK that automatically advances long-term task progress.

## ✨ Key Features

- 🤖 **Smart Phase Selection** - Automatically analyzes progress documents and selects the next phase to execute
- 🔄 **Subagent Dispatch** - Independently dispatches subtasks to avoid main agent context explosion
- 📊 **Structured Reporting** - Collects execution results and generates clear progress reports
- 📝 **Document-Driven** - Automatically executes tasks based on design and progress documents
- 🛠️ **Tool Integration** - Supports custom tool configuration (Playwright, Web Search, etc.)

## 📦 Installation

### Requirements

- Python >= 3.11
- Claude Agent SDK

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit the `.env` file and set the necessary environment variables:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from claude_agent_sdk import ClaudeAgentOptions
from deep_phase import PhaseRunner

async def main():
    # Configure options
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        permission_mode="acceptEdits",
    )
    
    # Create PhaseRunner
    runner = PhaseRunner(
        options=options,
        progress_path="path/to/progress.md",
        design_doc_path="path/to/tech.md"
    )
    
    # Execute next phase
    result = await runner.run_next_phase()
    
    print(f"Phase: {result.phase_name}")
    print(f"Status: {result.status}")
    print(f"Completed tasks: {result.completed_tasks}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Example

```bash
python main.py <workspace_path>
```

The example will automatically:
1. Read the `goal.md` file in the workspace
2. Analyze requirements and generate design and progress documents
3. Execute phases one by one until the project is complete

## 📁 Project Structure

```
DeepPhase/
├── src/
│   └── deep_phase/          # Core package
│       ├── analyzer.py      # Requirements analyzer
│       ├── runner.py        # Phase executor
│       ├── config.py        # Configuration management
│       ├── tool_loader.py   # Tool loader
│       ├── types.py         # Type definitions
│       ├── hooks/           # Hook functions
│       └── tools/           # Tool integrations
├── main.py                  # Main program example
├── config.yaml              # Configuration file
├── tests/                   # Test directory
├── docs/                    # Documentation
└── workspace/               # Working directory (ignored)
```

## 🔧 Configuration

Configure tools and options in `config.yaml`:

```yaml
tools:
  playwright:
    enabled: true
  zhipu_web:
    enabled: true
    api_key: ${ZHIPU_API_KEY}
```

## 📖 Documentation

- [Design Document Example](docs/design_example_simple/)
- [Progress Document Example](docs/design_example_origin/)

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

[MIT License](LICENSE)

## 🔗 Related Links

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [Claude API Documentation](https://docs.anthropic.com/)
