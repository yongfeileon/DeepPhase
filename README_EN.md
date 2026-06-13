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

### Run Example

#### Basic Usage

```bash
python main.py path/to/goal.md
```

#### Specify Target Code Directory

```bash
python main.py path/to/goal.md /path/to/code
```

#### Disable Git Operations (Safe Mode)

```bash
python main.py path/to/goal.md /path/to/code --deny-git
```

### Goal File and Code Directory Separation

DeepPhase supports separating **requirement documents** from **code directory**:

- **Goal File**: Markdown file describing requirements
- **Code Directory**: Where SubAgent actually performs code operations
- **Docs Directory**: Auto-generated under `_docs/` in goal file's parent directory

**Parameter Description**:

```bash
python main.py <goal_file> [target_dir] [--deny-git]
```

- `goal_file`: Path to goal.md file (required)
- `target_dir`: Code execution directory (optional, defaults to goal file's parent directory)
- `--deny-git`: Disable git operations

**Examples**:

```bash
# Requirements and code in same directory
python main.py ./workspace/goal.md

# Requirements and code separated
python main.py ./requirements/goal.md ./my-project

# Disable git operations
python main.py ./workspace/goal.md --deny-git
```

The program will automatically:
1. Read the specified goal file
2. **Use LLM to identify task type** (coding task or general task)
3. Analyze requirements and generate documents to `_docs/design/` under goal file's directory
   - **Coding tasks**: Generate tech.md and progress.md
   - **General tasks**: Generate progress.md only
4. Execute phases until completion (code operations in target directory)

### Real-time Interaction

DeepPhase supports real-time interaction during SubAgent execution:

#### Built-in Commands

- `/pause` - Pause execution
- `/resume` - Resume execution
- `/stop` - Stop execution

#### Natural Language Input

Input natural language directly during SubAgent execution, and the system will inject it into the current conversation:

```bash
$ python main.py workspace

[SubAgent] Implementing feature X...

> Please add error handling
[Status] Received, will inject after next message

[User Input] Please add error handling
[SubAgent] Sure, I'll add try-catch...
```

**How it works**:

- Uses **double-loop architecture**: outer loop manages phases, inner loop handles SubAgent messages
- User input is passed through a queue mechanism
- SubAgent checks the queue after processing current message and injects user input immediately
- No need to wait for current phase to end, can intervene in real-time

### Channel System

DeepPhase uses an extensible Channel system for I/O:

#### Built-in Channel

- **CLIChannel**: Command-line interaction (enabled by default)

#### Extending Channels

Implement custom Channels to integrate other communication methods (WebSocket, HTTP API, etc.):

```python
from deep_phase.channels import Channel, Message, MessageType

class CustomChannel(Channel):
    async def send(self, message: Message):
        # Send message to external system
        pass
    
    async def receive(self) -> str:
        # Receive external input
        pass

# Register Channel
channel_mgr.register_channel(CustomChannel())
```

Channel features:
- Broadcast messages to all active channels
- Command handling (`/pause`, `/stop`, etc.)
- Natural language input routing

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
