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

### 基本使用

```python
import asyncio
from claude_agent_sdk import ClaudeAgentOptions
from deep_phase import PhaseRunner

async def main():
    # 配置选项
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        permission_mode="acceptEdits",
    )
    
    # 创建 PhaseRunner
    runner = PhaseRunner(
        options=options,
        progress_path="path/to/progress.md",
        design_doc_path="path/to/tech.md"
    )
    
    # 执行下一个 phase
    result = await runner.run_next_phase()
    
    print(f"Phase: {result.phase_name}")
    print(f"状态: {result.status}")
    print(f"完成任务: {result.completed_tasks}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 运行示例

#### 基本用法

```bash
python main.py <workspace_path>
```

#### 禁用 git 操作（安全模式）

```bash
python main.py <workspace_path> --deny-git
```

程序会自动：
1. 读取 workspace 中的 `goal.md` 文件
2. **使用 LLM 识别任务类型**（编程任务 or 通用任务）
3. 分析需求并生成相应的文档
   - **编程任务**：生成技术文档（tech.md）和进度文档（progress.md）
   - **通用任务**：仅生成进度文档（progress.md）
4. 逐个执行 phase 直到项目完成

## 📁 项目结构

```
DeepPhase/
├── src/
│   └── deep_phase/              # 核心包
│       ├── analyzer.py          # 需求分析器（含意图识别）
│       ├── runner.py            # Phase 执行器
│       ├── prompt_builder.py    # Prompt 构建器
│       ├── config.py            # 配置管理
│       ├── tool_loader.py       # 工具加载器
│       ├── types.py             # 类型定义
│       ├── hooks/               # 钩子函数（含 git 拦截）
│       └── tools/               # 工具集成
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
