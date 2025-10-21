# 重构总结 / Refactoring Summary

## 概览 / Overview

本次重构将 Core-PPTAutomate 从双模式系统（PPT/HTML）转变为统一的 HTML-to-PPTX 工作流，灵感来自 claude-skills/pptx 项目。

This refactoring transforms Core-PPTAutomate from a dual-mode system (PPT/HTML) into a unified HTML-to-PPTX workflow, inspired by the claude-skills/pptx project.

## 核心变更 / Core Changes

### 1. 架构统一 / Unified Architecture

**之前 / Before:**
- 两种模式：PPT 模式（使用 python-pptx + 模板）和 HTML 模式（仅生成 HTML）
- 通过环境变量 `MODE` 切换
- 两个独立的端点：`/generate-ppt` 和 `/generate-html`

**现在 / After:**
- 单一流程：HTML 生成 → PPTX 转换
- 统一端点：`/generate`
- 无需模式切换

### 2. 技术栈更新 / Technology Stack Update

**移除 / Removed:**
- python-pptx（Python PPT 库）
- pptx_ea_font
- 模板系统（template-based generation）

**新增 / Added:**
- html2pptx.js（Node.js 库）
- Node.js 集成
- Playwright（用于 HTML 渲染）

### 3. 代码结构 / Code Structure

#### 新增文件 / New Files

```
src/
├── services/
│   ├── content_parser.py          # 解析对话数据
│   ├── html_slide_generator.py    # 生成 HTML 幻灯片
│   ├── pptx_converter.py          # 转换 HTML 到 PPTX
│   └── file_saver.py              # 统一文件保存
├── workflows/
│   └── presentation_workflow.py   # 工作流编排
└── prompts/
    └── html_slide_generator.py    # Prompt 模板
```

#### 删除文件 / Deleted Files

```
src/
├── services/
│   ├── html_generator/            # 旧 HTML 生成器
│   ├── html_saver/                # 旧 HTML 保存器
│   ├── ppt_generator/             # 旧 PPT 生成器
│   └── ppt_saver/                 # 旧 PPT 保存器
└── prompt/
    ├── html/                       # 旧 HTML prompt
    └── ppt/                        # 旧 PPT prompt
```

## 设计原则 / Design Principles

借鉴 claude-skills/pptx 的设计理念：

Inspired by claude-skills/pptx design philosophy:

1. **Web-Safe Fonts Only / 仅使用 Web 安全字体**
   - Arial, Helvetica, Times New Roman, Georgia
   - Courier New, Verdana, Tahoma, Trebuchet MS, Impact

2. **Color Guidelines / 色彩指南**
   - 选择 3-5 个匹配内容主题的颜色
   - 确保强对比度（WCAG AA 标准）
   - HTML 中使用 `#` 前缀，PptxGenJS 中不使用

3. **Layout Best Practices / 布局最佳实践**
   - 标准尺寸：720pt × 405pt (16:9)
   - 使用 Flexbox 进行响应式布局
   - 图表幻灯片优先使用两列布局
   - 避免垂直堆叠图表

4. **HTML Requirements / HTML 要求**
   - 所有文本必须在 `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` 标签内
   - 不使用手动符号列表（•, -, *）
   - 禁止 CSS 渐变（使用纯色或预渲染 PNG）
   - 禁止 SVG 或 canvas 元素
   - 背景/边框/阴影仅用于 `<div>` 元素

## 工作流程 / Workflow

```
用户请求 / User Request
    ↓
ContentParser (解析对话数据 / Parse conversation)
    ↓
HTMLSlideGenerator (生成 HTML 幻灯片 / Generate HTML slides)
    ↓
PPTXConverter (转换为 PPTX / Convert to PPTX)
    ↓
FileSaver (保存输出 / Save output)
    ↓
返回文件 / Return file
```

## API 变更 / API Changes

### 请求格式 / Request Format

保持不变 / Unchanged:

```json
{
  "userName": "用户名",
  "threadId": "线程ID",
  "conversation": [
    {
      "question": {"content": "问题"},
      "answer": {"content": "答案"}
    }
  ],
  "assets": {
    "indicatorCharts": [...],
    "sourceList": [...]
  }
}
```

### 响应格式 / Response Format

**之前 / Before:**
```json
{"fileId": "file.pptx"}  // PPT mode
{"fileId": "file.html", "mode": "html"}  // HTML mode
```

**现在 / After:**
```json
{"fileId": "file.pptx"}  // Always PPTX
```

## 安装步骤 / Installation Steps

### 1. Python 依赖 / Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Node.js 依赖 / Node.js Dependencies

```bash
# 全局安装 html2pptx
npm install -g ./refactor_ideas/pptx/html2pptx.tgz

# 验证安装
npm list -g @ant/html2pptx
```

### 3. 环境配置 / Environment Configuration

创建 `.env` 文件：

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
DEFAULT_LLM_DEPLOYMENT=gpt-5
DEFAULT_LLM_TEMPERATURE=1
```

### 4. 运行服务 / Run Service

```bash
# 开发模式
uvicorn app:app --reload --port 5056

# 生产模式
gunicorn -k uvicorn.workers.UvicornWorker app:app --bind=0.0.0.0:5056
```

## 测试 / Testing

```bash
# 运行测试
pytest tests/test_workflow.py -v

# 测试 API
curl -X POST http://localhost:5056/generate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## 文档 / Documentation

- **README.md**: 项目概览和使用指南
- **SETUP.md**: 详细安装步骤
- **MIGRATION.md**: 从旧版本迁移指南
- **CHANGELOG.md**: 版本变更记录
- **refactor_ideas/pptx/SKILL.md**: html2pptx 使用指南
- **refactor_ideas/pptx/html2pptx.md**: HTML 到 PPTX 转换详解

## 性能优化 / Performance Improvements

1. **简化架构**: 减少中间层，提高处理速度
2. **统一流程**: 消除模式切换开销
3. **更好的错误处理**: 统一的重试机制
4. **工作空间管理**: 自动清理临时文件

## 安全性 / Security

1. **输入验证**: 所有用户输入经过验证
2. **文件隔离**: 按用户哈希隔离输出文件
3. **日志记录**: 完整的操作日志（英文）
4. **错误处理**: 安全的错误信息返回

## 维护性 / Maintainability

1. **代码简洁**: 最少注释，关键位置注释用英文
2. **模块化**: 清晰的职责分离
3. **可测试**: 完整的单元测试覆盖
4. **文档完善**: 多种文档支持不同场景

## 下一步 / Next Steps

1. **运行测试**: 确保所有功能正常
2. **部署验证**: 在测试环境验证
3. **性能测试**: 负载测试和性能优化
4. **监控设置**: 配置日志和监控

## 问题排查 / Troubleshooting

### 常见问题 / Common Issues

1. **找不到 html2pptx 模块**
   ```bash
   npm install -g ./refactor_ideas/pptx/html2pptx.tgz
   export NODE_PATH=$(npm root -g)
   ```

2. **字体问题**
   - 仅使用 Web 安全字体
   - 检查 HTML 中的 font-family 设置

3. **渐变不显示**
   - CSS 渐变不转换到 PPTX
   - 使用纯色或预渲染 PNG 图片

4. **转换失败**
   - 检查 Node.js 版本 (>= 16)
   - 验证 html2pptx 安装
   - 查看日志文件

## 联系方式 / Contact

如有问题或建议，请通过以下方式联系：

For issues or suggestions:
- 查看文档：README.md, SETUP.md, MIGRATION.md
- 参考示例：refactor_ideas/pptx/
- 检查日志：查看详细错误信息

## 致谢 / Acknowledgments

本次重构深受 [claude-skills/pptx](https://github.com/anthropics/claude-skills) 项目的启发，采用了其设计理念、工作流程和最佳实践。

This refactoring is heavily inspired by the [claude-skills/pptx](https://github.com/anthropics/claude-skills) project, adopting its design principles, workflow, and best practices.

---

**版本 / Version**: 2.0.0  
**日期 / Date**: 2024-10-21  
**状态 / Status**: ✅ 完成 / Completed

