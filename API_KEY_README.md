# OpenAI API Key 测试和修复工具

这个工具集可以帮助你检查、测试和修复OpenAI API Key相关的问题。

## 文件说明

1. **fix_api_key.py** - 检查并修复.env文件中的API Key格式问题
2. **test_api_key.py** - 测试API Key是否可以成功连接OpenAI API
3. **test_api_with_proxy.py** - 使用代理测试API Key连接

## 使用方法

### 步骤1: 修复API Key格式

这个工具会检查并修复.env文件中API Key的格式问题，如换行符或空格。

```bash
python fix_api_key.py
```

根据提示进行操作，可能会要求您输入一个新的API Key。

### 步骤2: 测试API连接

测试您的API Key是否可以成功连接到OpenAI API。这个脚本会尝试多种方式进行连接测试。

```bash
python test_api_key.py
```

### 步骤3: 如果步骤2失败，尝试使用代理测试

如果直接连接失败，您可以尝试通过HTTP代理连接。

```bash
# 使用环境变量中的代理
python test_api_with_proxy.py

# 或指定一个代理
python test_api_with_proxy.py http://your-proxy-host:port
```

## 常见问题

### API Key格式问题

- API Key应该是一个连续的字符串，不包含换行符或空格
- 标准的OpenAI API Key通常以`sk-`开头
- 项目API Key可能以`sk-proj-`开头
- API Key的长度通常在40-100字符之间

### 网络连接问题

- 某些地区（如中国大陆）可能需要使用代理才能连接OpenAI API
- 设置HTTP_PROXY和HTTPS_PROXY环境变量可以帮助解决此问题
- 或使用`test_api_with_proxy.py`脚本指定代理

### API Key限制问题

- 免费版API Key可能有请求速率和用量限制
- 检查您的OpenAI账户余额和使用情况
- 尝试创建一个新的API Key

## 环境变量设置

.env文件中应该包含以下设置:

```
PORT=8000
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-3.5-turbo
VECTOR_DB=faiss
VECTOR_DB_PATH=./vector_db
LLM_MODEL_TYPE=openai
```

## 故障排除

1. **测试失败但API Key正确**：尝试增加超时时间或使用代理
2. **API Key格式异常**：确保没有额外的空格、换行符或其他非法字符
3. **网络连接问题**：检查您的网络是否可以连接到api.openai.com
4. **API Key权限问题**：确认您的API Key有适当的权限和余额

希望这些工具能帮助您解决API连接问题! 