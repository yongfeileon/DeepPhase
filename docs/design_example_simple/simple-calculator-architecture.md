# 简单计算器项目架构

## 项目目标

创建一个简单的 Python 计算器模块，包含基础的加减乘除功能。

## 技术栈

- Python 3.8+
- pytest（测试框架）

## 项目结构

```
calculator/
├── __init__.py
├── calc.py          # 计算器核心功能
└── test_calc.py     # 单元测试
```

## 核心功能

### calc.py

提供以下函数：
- `add(a, b)` - 加法
- `subtract(a, b)` - 减法
- `multiply(a, b)` - 乘法
- `divide(a, b)` - 除法（需处理除零错误）

## 测试要求

- 每个函数至少2个测试用例
- 测试除零异常处理
- 使用 pytest 框架
