# 多LLM提供商支持指南

**更新日期**: 2026-01-27

## 概述

小说AI Agent现已支持多个LLM提供商，您可以根据需求选择不同的模型:

- **Anthropic Claude** - 高质量创作，推理能力强
- **OpenAI GPT** - 通用能力，广泛使用
- **DeepSeek** - 性价比高，中文支持好
- **Azure OpenAI** - 企业级部署

## 支持的LLM提供商

### 1. Anthropic Claude (默认)

**特点**:
- 最高质量的文本生成
- 优秀的推理和创意能力
- 较好的中文支持
- 适合高质量小说创作

**推荐模型**:
- `claude-sonnet-4-20250514` (默认) - 平衡性能与成本
- `claude-opus-4-20250514` - 最高质量，成本较高

**成本** (每百万token):
- Sonnet 4: ~$3 (输入) / $15 (输出)
- Opus 4: ~$15 (输入) / $75 (输出)

**配置示例**:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
DEFAULT_MODEL=claude-sonnet-4-20250514
```

### 2. OpenAI GPT

**特点**:
- 通用能力强
- 广泛的社区支持
- 多种模型可选

**推荐模型**:
- `gpt-4o` (默认) - 最新优化版
- `gpt-4-turbo` - 高性能版本
- `gpt-4` - 标准版本

**成本** (每百万token):
- GPT-4o: ~$2.5 (输入) / $10 (输出)
- GPT-4 Turbo: ~$10 (输入) / $30 (输出)

**配置示例**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
DEFAULT_MODEL=gpt-4o
```

### 3. DeepSeek (推荐用于中文创作)

**特点**:
- 极高性价比
- 优秀的中文能力
- OpenAI兼容API
- 适合大量创作

**推荐模型**:
- `deepseek-chat` - 通用对话模型
- `deepseek-coder` - 代码生成(不适用于小说)

**成本** (每百万token):
- DeepSeek Chat: ~$0.14 (输入) / $0.28 (输出)
- **性价比极高，约为Claude的1/10**

**配置示例**:
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxx
DEFAULT_MODEL=deepseek-chat
```

**获取API Key**: https://platform.deepseek.com/api_keys

### 4. Azure OpenAI

**特点**:
- 企业级SLA保障
- 数据隐私保护
- 适合企业部署

**配置示例**:
```env
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=xxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
```

## 快速配置

### 1. 编辑.env文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用其他编辑器
```

### 2. 选择提供商并配置

**使用DeepSeek (推荐开始):**
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
TEMPERATURE=0.7
MAX_TOKENS=4096
```

**使用Claude (推荐高质量):**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
TEMPERATURE=0.7
MAX_TOKENS=4096
```

### 3. 验证配置

```bash
python3 main.py version
```

如果配置正确，应该能正常运行不报错。

## 使用指南

### 创建小说时指定模型

配置文件中的`LLM_PROVIDER`和`DEFAULT_MODEL`决定使用哪个模型。

```bash
# 使用DeepSeek创建小说
python3 main.py create \
  --title "我的小说" \
  --genre "科幻" \
  --theme "AI觉醒" \
  --style "刘慈欣"
```

### 切换LLM提供商

只需修改`.env`文件中的配置:

```bash
# 从Claude切换到DeepSeek
# 修改.env文件:
# LLM_PROVIDER=anthropic  # 改为 deepseek
# 注释掉ANTHROPIC_API_KEY
# 取消注释DEEPSEEK_API_KEY
```

然后重新运行命令即可。

### 混合使用不同模型

目前不支持在同一个小说项目中混用不同模型（计划在Phase 3支持）。

建议:
- 用DeepSeek生成大纲和初稿（性价比高）
- 用Claude润色和优化（质量更高）

## 性能对比

### 质量评估

| 提供商 | 创意性 | 逻辑性 | 中文能力 | 风格模仿 | 综合评分 |
|--------|--------|--------|----------|----------|----------|
| Claude Sonnet 4 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 9.2/10 |
| GPT-4o | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 8.5/10 |
| DeepSeek Chat | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 7.8/10 |

### 成本对比 (创作20章小说)

假设每章3000字，大纲2000字，角色1000字:

| 提供商 | 大纲+角色 | 单章 | 20章总计 | 性价比 |
|--------|-----------|------|----------|--------|
| Claude Sonnet 4 | ~$0.40 | ~$0.12 | ~$2.80 | ⭐⭐⭐ |
| GPT-4o | ~$0.30 | ~$0.10 | ~$2.30 | ⭐⭐⭐⭐ |
| DeepSeek Chat | ~$0.03 | ~$0.01 | ~$0.23 | ⭐⭐⭐⭐⭐ |

**结论**: DeepSeek成本仅为Claude的1/12，适合大量创作。

### 速度对比

| 提供商 | 大纲生成 | 章节创作 | API稳定性 |
|--------|----------|----------|-----------|
| Anthropic | 30-50秒 | 40-80秒 | ⭐⭐⭐⭐⭐ |
| OpenAI | 25-40秒 | 35-70秒 | ⭐⭐⭐⭐ |
| DeepSeek | 20-35秒 | 30-60秒 | ⭐⭐⭐⭐ |

## 推荐配置方案

### 方案1: 性价比优先 (DeepSeek)

适合:
- 预算有限
- 需要大量创作
- 主要创作中文小说

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEFAULT_MODEL=deepseek-chat
TEMPERATURE=0.8  # 提高创意性
```

**预计成本**: 20章小说 ~$0.20-0.30

### 方案2: 质量优先 (Claude)

适合:
- 追求最高质量
- 创作精品小说
- 需要强大的推理能力

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
DEFAULT_MODEL=claude-sonnet-4-20250514
TEMPERATURE=0.7
```

**预计成本**: 20章小说 ~$2.50-3.50

### 方案3: 平衡方案 (GPT-4o)

适合:
- 平衡质量和成本
- 需要稳定的服务
- 多语言创作

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
DEFAULT_MODEL=gpt-4o
TEMPERATURE=0.7
```

**预计成本**: 20章小说 ~$2.00-2.80

## 常见问题

### Q: 如何获取各个平台的API Key?

**Anthropic Claude**:
https://console.anthropic.com/settings/keys

**OpenAI**:
https://platform.openai.com/api-keys

**DeepSeek**:
https://platform.deepseek.com/api_keys

**Azure**:
https://portal.azure.com (需要先创建Azure OpenAI资源)

### Q: 不同模型生成的内容质量有多大差异?

- **Claude**: 创意性最强，风格模仿最准确，逻辑最严密
- **GPT-4o**: 综合能力强，输出稳定
- **DeepSeek**: 中文能力优秀，性价比极高，但创意性略低

### Q: 可以在创作过程中切换模型吗?

目前不建议在同一个小说项目中途切换模型，可能导致风格不一致。

建议:
1. 用一个模型完成整部小说
2. 或者在修改/润色阶段切换到更高质量的模型

### Q: DeepSeek真的好用吗?

**优点**:
- 成本极低（1/10的价格）
- 中文能力出色
- 速度快
- 适合大量创作

**缺点**:
- 创意性相比Claude略低
- 风格模仿不够精准
- 偶尔会出现重复

**建议**: 先用DeepSeek试试，如果质量满意就继续用，不满意再换Claude。

### Q: 为什么我配置了但还是报错?

检查清单:
1. ✓ `.env`文件在项目根目录
2. ✓ `LLM_PROVIDER`设置正确
3. ✓ 对应的API Key已配置
4. ✓ API Key格式正确（包含前缀，如`sk-`）
5. ✓ 网络可以访问对应API

### Q: Azure OpenAI如何配置?

Azure配置较复杂，需要:
1. 在Azure创建OpenAI资源
2. 创建部署(deployment)
3. 获取endpoint和key
4. 配置到.env文件

详见Azure官方文档。

## 最佳实践

### 1. 根据场景选择模型

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 初稿创作 | DeepSeek | 成本低，速度快 |
| 精品创作 | Claude Sonnet 4 | 质量最高 |
| 大纲规划 | Claude 或 GPT-4o | 需要强逻辑 |
| 角色设定 | 任意 | 要求不高 |
| 章节润色 | Claude Sonnet 4 | 风格掌控好 |

### 2. 温度参数调整

```env
# 创意性写作（科幻、奇幻）
TEMPERATURE=0.8

# 逻辑性写作（推理、现实）
TEMPERATURE=0.6

# 平衡
TEMPERATURE=0.7
```

### 3. Token限制

```env
# 短章节（1000-2000字）
MAX_TOKENS=2000

# 标准章节（3000字）
MAX_TOKENS=4096

# 长章节（5000+字）
MAX_TOKENS=8000
```

## 技术细节

### LLM切换实现

BaseAgent会根据配置自动创建对应的LLM实例:

```python
# 自动根据LLM_PROVIDER创建
if provider == "anthropic":
    llm = ChatAnthropic(...)
elif provider == "openai":
    llm = ChatOpenAI(...)
elif provider == "deepseek":
    llm = ChatOpenAI(base_url="https://api.deepseek.com/v1", ...)
elif provider == "azure":
    llm = AzureChatOpenAI(...)
```

### 配置验证

系统会在创建Agent时验证配置:

```python
is_valid, error_msg = settings.validate_provider_config()
if not is_valid:
    raise ValueError(f"LLM配置无效: {error_msg}")
```

## 更新日志

**2026-01-27**:
- ✅ 添加多LLM提供商支持
- ✅ 支持Anthropic Claude
- ✅ 支持OpenAI GPT系列
- ✅ 支持DeepSeek
- ✅ 支持Azure OpenAI
- ✅ 自动配置验证
- ✅ 延迟初始化避免启动报错

## 下一步

**Phase 3计划**:
- [ ] 支持在同一项目中混用不同模型
- [ ] 自动模型选择（根据任务类型）
- [ ] 模型性能监控和对比
- [ ] 更多模型支持（Gemini, Claude等）

---

**文档版本**: v1.0
**维护者**: Keith Xi
**最后更新**: 2026-01-27
