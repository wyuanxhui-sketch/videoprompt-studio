# VideoPrompt Studio v0.3 · 云端 AI 智能分镜版

中文 Streamlit 分镜工具，保留 v0.2 的规则生成、五种风格、5/7/10 秒建议时长、十列表格编辑增删、逐镜头提示词和 Excel/CSV 导出，新增 DeepSeek 官方 API 智能分镜。只修改 v0.3 开发目录。

不开发视频生成、图片生成、数据库或用户账户。开发验收未调用付费 API，未自动部署。

## Windows 本地启动

```powershell
Set-Location 'E:\AI学习课程\AI视频提示词工作流_v0.3_API开发版'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

访问 http://127.0.0.1:8501 ，Ctrl+C 停止。当前目录已安装项目内 `.venv`。

新环境安装（推荐 Python 3.12）：

```powershell
py -3.12 -m venv .venv
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = Join-Path (Get-Location) '.tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

若 ensurepip 失败，可通过已安装的 pip 修复：

```powershell
py -3.12 -m pip --python .\.venv\Scripts\python.exe install --no-cache-dir -r requirements.txt
```

运行依赖使用 Streamlit、pandas、openpyxl；DeepSeek 客户端采用 Python 标准库，无新增 SDK。为满足 Community Cloud 文档的兼容范围，对已有间接依赖增加 `protobuf>=5.26.1,<6` 约束。

## 使用

默认规则模式无需密钥和网络。输入文案或载入原佛光寺示例，点击“生成分镜”。规则按幕次、已识别主体和视觉事件拆分，不能保证复杂剧情的语义理解。

AI智能模式：输入完整文案、视频风格、单镜头建议时长、可选目标总时长与连续性要求，选择模型、输入自己的 API Key，再点击“开始AI生成”。刷新、修改参数、编辑表格或下载文件不自动调用 API。页面含第四至第六幕验收文案，可复制使用。

AI 系统提示词要求理解剧情、幕次、地点、人物和视觉事件，规划景别、机位、运镜与时长，保持跨幕人物身份、外貌、运动方向、服装状态和空间连续。要求区分真实建筑构件与现代斗拱状展陈；无可靠资料时不得编造双槽具体结构、构件数量、尺度、年代或材质。复杂变装、渐变和穿梭镜头建议分段生成与后期拼接。目标总时长为规划目标，页面显示编辑后的实际总时长供核对。

列顺序严格为：**镜头号、地点、画面内容、景别、机位、运镜、时长（秒）、对话、备注、配图**。

API 返回 `{"shots": [...]}` JSON，服务端校验十列字段、类型、编号顺序、时长范围、镜头数，以及备注五段内容：AI视频生成提示词、音效、转场、连续性约束、后期制作。配图留空。输出异常明确报错，保留旧表格；可以手动切换规则模式，不会伪造成功。

表格支持人工编辑、新增和删除，下载与复制使用当前编辑结果。修改镜头参数后需同步修改备注。重新生成成功会替换当前表格。配图可人工填写参考路径或链接，本版不加载图片。Excel 将输入作为文本保存，CSV 为 UTF-8 BOM；保留 v0.2 CSV 行为，电子表格打开 CSV 时公式前缀可能被识别为公式。

## BYOK、安全与费用

- 在网页 AI 模式的密码输入框填写**自己的 DeepSeek API Key**。调用可能产生费用，由该密钥所属账户承担；文案及连续性要求会发送至 DeepSeek。
- 浏览器仅向 Streamlit 提交会话输入，API 由服务端请求固定 HTTPS 官方端点；拒绝 HTTP 重定向。
- 密钥只用于当前会话内存及请求头，不写入代码、日志、文件、URL、导出或共享缓存。不同用户和标签页会话不共享密钥。刷新建立新会话、离开或服务重启后允许重新输入。会话释放由 Streamlit 管理，不承诺关闭标签页时立即内存擦除。
- 不缓存带密钥的请求或 API 客户端，不提供持久化密钥存储。
- 默认公开 BYOK 行为：服务器即使存在 `DEEPSEEK_API_KEY`，访客也不能使用开发者密钥。
- 公开部署前检查已彻底移除本地环境变量回退路径：即使设置 `VIDEOPROMPT_LOCAL_DEV=1` 和 `DEEPSEEK_API_KEY`，程序也不会读取或启用开发者密钥。现在本地与公开部署均仅使用网页 BYOK。
- Cloud Secrets 不填写开发者密钥或开发标志。使用 HTTPS，关闭记录请求头、表单内容的代理或调试日志。配置隐藏浏览器中的未处理异常详情；这并不代替服务端日志安全，项目本身不打印密钥、文案或响应。

## 官方 API 核实

核实日期：2026-10-15。

- [模型与价格](https://api-docs.deepseek.com/quick_start/pricing/)：当前模型 `deepseek-flash`、`deepseek-v4-pro` 均支持 JSON 输出。默认 Flash，官方输入与输出价格较低，适合本项目中文文本分镜。实际费用以官方价格和账户为准，价格可能变更。
- [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)：OpenAI 兼容 `POST https://api.deepseek.com/chat/completions`。非流式，明确设置 `thinking.type=disabled` 控制输出与成本。
- [JSON Output](https://api-docs.deepseek.com/guides/json_mode/)：设置 `response_format={"type":"json_object"}`，提示词要求 JSON 并提供十列示例。仍需业务校验，空响应、错误 JSON、字段缺失和截断均报错。

模型在网页选择，不沿用未按当前官方文档核实的旧模型 ID。将来模型变更时，重新核实后维护 `ai_storyboard.py` 允许列表；程序不自动查询模型或发起额外请求。

## 成本限制与重复保护

- 文案最多8000字符，连续性1000字符；最大镜头数1–24，默认12。
- 目标总时长1–600秒，0表示不指定；AI输出单镜头时长校验1–60秒。
- 单次输出8192 Token，响应最多512000字节，网络操作超时60秒。
- **自动重试0次**。超时可能发生在供应商已接受或计费之后，请核对账户后手动重试。
- 当前会话记录不含密钥的请求指纹和运行标记，相同参数再次点击会拦截重复调用，失败后也保留保护。再次调用需先点击“解除相同请求保护”，再点击“开始AI生成”；解除本身不调用 API。修改生成参数可以提交不同请求。
- 保护仅限当前会话，刷新或新会话会重置，不是供应商计费幂等保证。避免跨标签页重复提交。
- 页面显示可获得的输入、输出、总 Token；未提供用量不代表免费。JSON校验失败时仍显示可获得的用量。

## 自动化测试（全部 Mock）

```powershell
Set-Location 'E:\AI学习课程\AI视频提示词工作流_v0.3_API开发版'
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = Join-Path (Get-Location) '.tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m compileall -q app.py ai_storyboard.py generator.py storyboard.py tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

共42项测试全部通过：原15项、AI相关23项、部署安全4项。覆盖正常JSON、错误JSON、字段缺失、空响应、超时、无密钥、HTTP/网络错误、截断、类型/数量/长度限制、Token统计、密钥反射拦截、重定向拒绝、公开模式禁用开发者密钥、多用户隔离、新会话密钥重新输入、按钮调用与重复保护、编辑不调用API、失败保留旧表、人工编辑增删与Excel/CSV导出。部署检查增加误设开发环境变量时仍禁用回退、两用户文案/响应/导出隔离、实际Git忽略规则和依赖/config约束验证。

测试密钥为 `mock-*` 假值，网络边界被Mock，网页测试禁止真实请求。第四至第六幕的合成响应模拟5个叙事镜头，验证提示词传输、结构解析及编辑导出链路。**Mock不能证明真实模型的剧情理解能力或建筑表达准确性。**

未来仍需用户授权真实API验证：账户模型可用性、官方端点兼容、真实耗时/费用/Token用量、实际叙事拆分、人物/空间/服装连续性及双槽和斗拱的建筑表达；需要可靠实拍与图纸人工核对。公开部署后的HTTPS、代理日志和真实浏览器会话行为也需环境验证。

## 文件

- 修改 `app.py`：中文两模式界面、BYOK、状态和编辑导出。
- 新增 `ai_storyboard.py`：官方API、系统提示词、限制、JSON校验与错误处理。
- 修改 `storyboard.py`：保留规则后端，备注补充后期建议。
- 新增 `tests/test_ai_storyboard.py`：Mock客户端及Streamlit界面验收。
- 修改 `README.md`：使用、安全、费用、测试和真实验证边界。
- `generator.py` 和原两个测试文件保持不变。部署检查修改 `requirements.txt`、`.gitignore`、`.streamlit/config.toml`，增加 `tests/test_deployment.py`；没有开发新版本或新增业务功能。

Linux可创建Python3.12虚拟环境，安装requirements后执行 `.venv/bin/python -m streamlit run app.py`。

## Community Cloud 公开部署前检查（2026-10-15）

结论：可作为面向非敏感文案的公开 BYOK 工具部署。严格私密文档服务不在当前安全边界内，见下面的下载链接限制。未上传 GitHub，未创建 Cloud 应用，未调用付费 API。

### 兼容性与入口

- 根目录 `app.py` 是 Cloud 入口，与 requirements 和其它三个源码文件放在同一层；无 Windows 专属运行依赖或绝对本地路径读取，无需 packages.txt。
- Python3.12 本地测试42/42通过，compileall通过，pip check无冲突；实际protobuf为5.29.6。
- 已核对发行包：Streamlit1.65.0与openpyxl3.1.5为通用wheel，pandas3.0.6有CPython3.12 Linux manylinux wheel，protobuf5.29.6有Linux wheel。
- Linux兼容结论依据源码、依赖元数据和发行包检查；本次没有Linux运行环境，未实际完成Linux或Cloud构建。部署时在Advanced settings明确选择Python3.12。
- 依据：[Cloud部署设置](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)、[依赖说明](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)、[Cloud兼容限制](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)。

### 会话与下载边界

密钥只位于当前会话的密码widget状态以及API函数局部参数/请求头，app不保留独立全局密钥变量；导入模块没有跨用户的可变数据缓存或API客户端。用户文案、分镜、用量和请求保护状态均按当前Streamlit会话管理。导出函数通过BytesIO或bytes生成文件，不落盘。Mock证明两用户的展示和生成/导出内容不串会话。

**原生 `st.download_button` 的边界：**当前Streamlit1.65.0会将下载bytes放入进程的媒体内存存储，URL使用内容标识。其 `/media/...` 路由不核验下载者是否为生成文件的会话，因此持有或能推算有效下载链接的人可能取得文件。AppTest中的导出内容隔离不等于HTTP下载鉴权。没有账户系统，不能承诺下载文件只有当前用户可访问。链接和文案不要包含敏感个人资料，也不要传播有效下载链接。为遵守本次不新增功能或重构的要求，保留原生导出；若目标是敏感文档的严格访问控制，当前不能直接用于该目的。

代码检查未发现将密钥写入日志、文件、URL、缓存的路径；本次文件扫描未发现真实API密钥。外部平台、代理和DeepSeek自身的日志/数据处理需要按各自配置与政策评估，不在本地Mock验证范围内。

### GitHub上传白名单

只上传以下12个文件，保持相对目录结构：

```text
app.py
ai_storyboard.py
storyboard.py
generator.py
requirements.txt
README.md
.gitignore
.streamlit/config.toml
tests/test_generator.py
tests/test_storyboard.py
tests/test_ai_storyboard.py
tests/test_deployment.py
```

不要上传整个开发目录。.gitignore已排除.venv、.tmp、__pycache__、.env及变体、secrets.toml、日志、缓存、证书/密钥文件、个人数据目录与常见导出文件。**.gitignore按路径过滤，不能识别藏在源码中的密钥，也不会删除已提交历史中的秘密**；以后每次提交仍应检查差异。本目录尚不是Git仓库，本次无法审计未来仓库或已有远端的历史；不要复制带秘密的旧仓库历史，也不要用git add -f绕过排除规则。

Cloud部署参数：入口app.py、Python3.12、Secrets留空（本项目无需开发者密钥）。不要手动设置只监听127.0.0.1的本地启动参数到云端，Cloud会管理启动和端口。
