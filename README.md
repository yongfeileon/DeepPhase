# DeepPhase

[English](README_EN.md) | 简体中文

基于 Claude Agent SDK 的智能 Phase 执行器，自动推进长程任务进度。

## ✨ 核心特性

- 🤖 **智能 Phase 选择** - 自动分析进度文档，选择下一个待执行的 phase
- 🧠 **任务意图识别** - 基于 LLM 自动识别编程任务或通用任务
- 🔄 **Subagent 派发** - 独立派发子任务，避免主 agent context 爆炸
- 🔒 **安全控制** - 支持禁用 git 操作，保护代码仓库安全
- 📊 **结构化汇报** - 收集执行结果，生成清晰的进度报告
- 📝 **文档驱动** - 基于设计文档和进度文档自动执行任务
- 🛠️ **工具集成** - 支持自定义工具配置（Playwright、Web Search 等）

## 📦 安装

### 环境要求

- Python >= 3.11
- Claude Agent SDK

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的环境变量：

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

## 🚀 快速开始

### 运行示例

#### 基本用法

```bash
python main.py path/to/goal.md
```

#### 指定目标代码目录

```bash
python main.py path/to/goal.md /path/to/code
```

#### 禁用 git 操作（安全模式）

```bash
python main.py path/to/goal.md /path/to/code --deny-git
```

### Goal 文件与代码目录分离

DeepPhase 支持将**需求文档**与**代码目录**分离：

- **Goal 文件**：描述需求的 markdown 文件
- **代码目录**：SubAgent 实际执行代码操作的位置
- **文档目录**：自动生成在 goal 文件所在目录的 `_docs/` 下

**参数说明**：

```bash
python main.py <goal_file> [target_dir] [--deny-git]
```

- `goal_file`：goal.md 文件路径（必需）
- `target_dir`：代码执行目录（可选，默认为 goal 文件所在目录）
- `--deny-git`：禁用 git 操作

**示例**：

```bash
# 需求和代码在同一目录
python main.py ./workspace/goal.md

# 需求和代码分离
python main.py ./requirements/goal.md ./my-project

# 禁用 git 操作
python main.py ./workspace/goal.md --deny-git
```

程序会自动：
1. 读取指定的 goal 文件
2. **使用 LLM 识别任务类型**（编程任务 or 通用任务）
3. 分析需求并生成相应的文档到 goal 文件所在目录的 `_docs/design/`
   - **编程任务**：生成技术文档（tech.md）和进度文档（progress.md）
   - **通用任务**：仅生成进度文档（progress.md）
4. 逐个执行 phase 直到项目完成（代码操作在目标目录进行）

### 实时交互

DeepPhase 支持在 SubAgent 执行过程中进行实时交互：

#### 内置命令

- `/pause` - 暂停执行
- `/resume` - 恢复执行
- `/stop` - 停止执行

#### 自然语言输入

在 SubAgent 执行过程中直接输入自然语言，系统会将输入注入到当前对话中：

```bash
$ python main.py workspace

[SubAgent] 正在实现功能 X...

> 请添加错误处理
[状态] 已接收，将在下一条消息后注入

[用户输入] 请添加错误处理
[SubAgent] 好的，我会添加 try-catch...
```

**工作原理**：

- 采用**双循环架构**：外循环管理 phase，内循环处理 SubAgent 消息
- 用户输入通过队列机制传递
- SubAgent 在处理完当前消息后检查队列，立即注入用户输入
- 无需等待当前 phase 结束，可在执行过程中实时干预

### Channel 系统

DeepPhase 使用可扩展的 Channel 系统处理输入输出：

#### 内置 Channel

- **CLIChannel**：命令行交互（默认启用）

#### 扩展 Channel

可以实现自定义 Channel 接入其他通信方式（如 WebSocket、HTTP API 等）：

```python
from deep_phase.channels import Channel, Message, MessageType

class CustomChannel(Channel):
    async def send(self, message: Message):
        # 发送消息到外部系统
        pass
    
    async def receive(self) -> str:
        # 接收外部输入
        pass

# 注册 Channel
channel_mgr.register_channel(CustomChannel())
```

Channel 支持：
- 消息广播到所有活跃 channel
- 命令处理（`/pause`, `/stop` 等）
- 自然语言输入路由

## 📁 项目结构

```
DeepPhase/
├── src/
│   └── deep_phase/              # 核心包
│       ├── analyzer.py          # 需求分析器（含意图识别）
│       ├── runner.py            # Phase 执行器
│       ├── prompt_builder.py    # Prompt 构建器
│       ├── progress_tracker.py  # 进度追踪器
│       ├── config.py            # 配置管理
│       ├── tool_loader.py       # 工具加载器
│       ├── types.py             # 类型定义
│       ├── hooks/               # 钩子函数（含 git 拦截）
│       ├── tools/               # 工具集成
│       └── channels/            # Channel 系统
│           ├── base.py          # Channel 基类
│           ├── manager.py       # Channel 管理器
│           └── cli_channel.py   # CLI Channel
├── prompts/                     # Prompt 模板
│   ├── intent_detector.md       # 意图识别
│   ├── analyzer.md              # 编程任务分析
│   ├── subagent_task.md         # 编程任务执行
│   ├── general_analyzer.md      # 通用任务分析
│   └── general_subagent_task.md # 通用任务执行
├── main.py                      # 主程序
├── config.yaml                  # 配置文件
├── tests/                       # 测试目录
├── docs/                        # 文档
└── workspace/                   # 工作目录（被忽略）
```

## 🔧 配置

在 `config.yaml` 中配置工具和选项：

```yaml
# 安全配置
security:
  deny_git: false  # 设为 true 禁用所有 git 操作

# Prompt 配置
prompts:
  intent_detector: "prompts/intent_detector.md"  # 意图识别
  coding:                                        # 编程任务
    analyzer: "prompts/analyzer.md"
    subagent_task: "prompts/subagent_task.md"
  general:                                       # 通用任务
    analyzer: "prompts/general_analyzer.md"
    subagent_task: "prompts/general_subagent_task.md"

# 工具配置
tools:
  playwright:
    enabled: true
  zhipu_web:
    enabled: true
    replace_builtin: true
```

### 配置优先级

命令行参数 > 配置文件，例如：
- `--deny-git` 会覆盖 `config.yaml` 中的 `security.deny_git` 设置

## 📖 文档

- [设计文档示例](docs/design_example_simple/)
- [进度文档示例](docs/design_example_origin/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 🔗 相关链接

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [Claude API 文档](https://docs.anthropic.com/)
