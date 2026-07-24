---
name: single-file-security-scan
description: 当用户要求审查/扫描/审计单个文件的安全问题时使用。
---

# 单文件安全扫描

分析用户提供的一个文件（文件路径，或直接粘贴的文件内容），把安全相关的观察点整理成结构化 JSON 输出。每个观察点都带标签，并落在精确的行号和原文片段上。

这个技能是**一个观察者，不是一个预言家**。这个区分就是全部要点——往下读。

## 最重要的一条规则

**只报告你能直接在文件里看到的东西。绝不推测可能出什么问题。**

为什么重要：安全测试人员读你的输出时，需要相信每一行都扎根于文件里真实存在的内容。你一旦写出"这里可能存在 X 漏洞""攻击者可能 Y"，就已经离开了证据、进入了猜测——而猜测会带来虚假的确定性、噪音，以及浪费测试人员时间的发现。测试人员有你没有的上下文（威胁模型、运行环境、什么真正可达）。你的任务是做一个精确、穷尽的观察者，让他们自己去做风险判断。

具体来说：

- 每个观察点必须给出精确的行号，并附上你看到的原文片段。
- "fact"（事实）字段描述字面上存在的东西——不是它暗示什么，也不是它可能造成什么后果。
- 不赋予严重程度、风险等级、可能性或可利用性。
- 不使用这类词：可能、或许、潜在、容易、不安全、危险、应该、建议、考虑、注意、"攻击者可能"、"会导致"。
- 不按"重要性"对发现分组或排序。
- 不报告"缺失"（"没有输入校验""缺少错误处理""没有鉴权"）。缺失是对"本该有什么"的推断——不是对"实际有什么"的观察。只报告文件里实际存在的东西。
- 看不到的东西，就不报。

### 事实 vs 风险——举例

不要写这种推测：

- "第 12 行硬编码了 API key——如果仓库公开可能泄露。"
- "用了 MD5——不安全的哈希，存在碰撞攻击风险。"
- "eval(user_input)——潜在的远程代码执行。"
- "SQL 用字符串拼接构造——很可能存在注入。"

要写这种事实：

- 第 12 行：变量 `API_KEY` 被赋值为字符串字面量 `sk-live-9f8a7c`。标签：`hardcoded-secret`。
- 第 34 行：调用 `hashlib.md5(payload)`，参数为 `payload`。标签：`crypto-operation`。
- 第 58 行：`eval(data["expr"])`，其中 `data` 是解析后的 JSON 请求体。标签：`dynamic-code-exec`。
- 第 71 行：SQL 字符串通过 `f"SELECT * FROM users WHERE id={uid}"` 构造，插值了变量 `uid`。标签：`database-query`。

好的事实只说这一行上有什么，然后就停下。它命名"看到了什么"，而不是"这对安全意味着什么"。

## 预定义标签集

只用下面这些标签。每个标签描述的是一类**观察**，永远不是风险结论。

| 标签 | 观察到什么 |
|---|---|
| `hardcoded-secret` | 文件里写死的凭据、API key、token、密码、私钥、连接串 |
| `network-endpoint` | URL、IP 地址、域名、host:port、主机名 |
| `network-io` | 网络操作：HTTP 请求、socket 打开、连接、fetch、服务端监听 |
| `crypto-operation` | 加密原语调用：哈希、加解密、签名/验签、HMAC、随机数生成 |
| `crypto-configuration` | 写明的加密参数：算法名、模式、密钥长度、IV/nonce、填充、迭代次数 |
| `signature-verification` | 文件/数据的签名与完整性校验：校验和比对、GPG/数字签名验证、HMAC 与预期值比对等 |
| `dynamic-code-exec` | eval、exec、反射、动态 import/加载、代码生成、执行代码的模板渲染 |
| `process-execution` | 起外部进程/命令：exec、system、popen、subprocess、shell 调用 |
| `serialization` | 结构化数据的序列化/反序列化（pickle、marshal、对外部数据的 json.loads、unserialize） |
| `compression` | 压缩与解压操作：gzip、zip、zlib、tar、unzip、gunzip、bzip2 等的压缩或解压 |
| `filesystem-io` | 文件读写/创建/删除/移动，以及涉及的路径 |
| `database-query` | SQL/NoSQL 查询和语句、ORM 查询构造 |
| `input-parsing` | 读取外部/不可信输入：命令行参数、环境变量、HTTP 请求体/头/参数、stdin、上传文件 |
| `authentication-mechanism` | 认证逻辑：登录、登出、token 校验、密码核验、凭据检查 |
| `session-management` | session、token、cookie、JWT 处理 |
| `credential-generation` | 用随机源生成认证凭据：token、密码、API key、密钥、会话 ID 等（如 secrets.token_*、random 拼接、uuid） |
| `password-complexity` | 密码复杂度校验：长度阈值、大小写/数字/符号要求、强度正则等检查 |
| `permission-operation` | 权限/特权变更：chmod、chown、setuid、sudo、umask、ACL 变更 |
| `configuration-value` | 写明的值得注意的设置：调试开关、布尔开关、verbose 模式、默认值（如 `verify_ssl=false`） |
| `logging` | 日志语句——记录了什么数据（输入值、错误、标识符） |
| `comment-metadata` | 泄露信息的注释/元数据：内部主机名、基础设施细节、安全 TODO、版本号 |

如果某个观察确实匹配不上任何标签，仍要报告（以免漏点），但标签用 `other-observation`，并精确描述你看到了什么。优先用最接近的具体标签，而非 `other-observation`。 当一处同时符合 `crypto-operation`（验签原语）和 `signature-verification`（校验文件/数据完整性）时，归到更具体的 `signature-verification`。

标签标的是**观察**，不是结论。`crypto-operation` 的意思是"这里有一个加密调用"——不是"这个加密很弱"。`process-execution` 的意思是"这里起了一个进程"——不是"这很危险"。让标签只描述实际存在的东西。

## 输出格式

输出一个 JSON 对象。可以在它前面加一句简短引语，但 JSON 才是交付物。结构：

```json
{
  "input_mode": "path",
  "file": "/给定的/绝对/路径",
  "language_or_type": "python",
  "total_lines": 120,
  "summary": {
    "total_points": 5,
    "tag_counts": { "hardcoded-secret": 1, "network-endpoint": 2 }
  },
  "points": [
    {
      "tag": "hardcoded-secret",
      "line": 12,
      "snippet": "API_KEY = \"sk-live-9f8a7c...\"",
      "fact": "第 12 行，变量 `API_KEY` 被赋值为以 `sk-live-9f8a7c` 开头的字符串字面量。"
    }
  ]
}
```

字段规则：

- `input_mode`：`"path"`（用户给的是文件路径）或 `"content"`（用户直接给了文件内容）。
- `file`：`input_mode` 为 `path` 时，原样照抄用户给的路径；为 `content` 时填 `"inline"`。
- `language_or_type`：根据内容/扩展名做的最佳判断；不清楚就写 `unknown`。这是关于文件的事实，不是判断。
- `total_lines`：你读到的行数。
- `summary.tag_counts`：每个标签的计数——一个事实性的统计，不是风险排序。
- `points[].tag`：上面标签集里的一个。
- `points[].line`：观察点所在的行。跨多行的观察，用起始行。
- `points[].snippet`：该行的原文，逐字照抄，让测试人员能找到它。长行用 `…` 截断。
- `points[].fact`：一句话，只陈述存在什么。不带风险语言。每个论断都要落在 snippet 上。

按行号升序排列各点，方便测试人员对照文件从上往下读。

`fact` 字段用中文写。

## 工作流

1. 先判断输入形式：用户给的是**文件路径**，还是**直接粘贴的文件内容**。
2. 拿到完整内容：
   - **文件路径：** 用 Read 工具直接读取整个文件。**不要用 grep、glob 或任何搜索工具去找关键词。** 一次读不完就分段顺序读，合起来覆盖每一行--仍然是读，不是搜。
   - **文件内容：** 以用户给的全部内容为准，逐行分析；不要再去读别的文件或搜索。
   - 两种形式都不要打开或搜索其他文件。记录真实的 `total_lines`。

   为什么不搜：grep 只能命中你提前想到的关键词（一张关键词表）。它会悄悄漏掉所有不匹配你模式的东西——不按套路命名的东西、新的构造、只有结合上下文才看得出的观察。本技能的价值在于对文件里实际存在的东西做完整、真实的观察。搜索会把它变成一个关键词匹配器，毁掉它承诺的穷尽性。把整个文件读进来，看到那里有什么。

3. 逐行扫描。对每一个你具体看到的安全相关的东西，记一个点：选最合适的标签、记行号、抄原文片段、写事实。
4. 在"只讲事实"的规则内尽量穷尽——测试人员宁可看到 30 条有根有据的观察，也不要 5 条花哨的。但每个点都必须有据可查；绝不拿推测来凑数。
5. 统计标签，组装 JSON。
6. 调用脚本记录结果。将完整的 JSON 字符串作为唯一参数，在工作目录执行：
   ```bash
   python <skill_dir>/scripts/collect_result.py '<json_string>'
   ```
   脚本会自动创建 `.secscan/` 目录并追加到 `.secscan/results.json`。
   - `content` 模式（`file: "inline"`）也会写入，key 为 `"inline"`。
   - 同一文件重扫会覆盖更新。
   - 脚本会输出 `✓ 已记录: <file>` 或 `✗ 写入失败: ...`。
7. 输出 JSON 给用户。
8. 如果观察不到任何安全相关的东西，仍输出 JSON，`"points": []`，并加一个顶层 `"note": "未观察到安全相关内容"`。

## 边界——什么时候要忍住不写风险

即使某个东西看起来明显有风险，也要忍住。测试人员会看到 `eval(request_data)` 被标成 `dynamic-code-exec`、挂在精确的行上——他们自己能得出结论。你加上"远程代码执行风险"不会增加任何真实信息，还可能说错：也许输入在上游已被完全信任和校验过，而你在单个文件里看不到这些。陈述事实；把结论留给人类。

## 边界情况

下列主要针对"文件路径"模式；"文件内容"模式下用户给什么就分析什么，不涉及路径解析。

- **路径是个目录：** 不要递归或搜索。输出 JSON，带 `"note": "路径是目录；本技能只分析单个文件"` 和空的 `points` 数组，然后向用户要具体文件。
- **文件不存在 / 读不了：** 输出 JSON，`note` 说明发生了什么，`points` 为空。不要编造内容。
- **二进制 / 非文本文件**（图片、编译产物、压缩包）：输出 JSON，`points` 为空，`"note": "文件似乎是二进制/非文本；未分析"`。不要猜内容。
- **压缩成一行或超长行：** 抄一段有代表性的片段，用 `…` 截断；行号仍能定位。
- **只有注释或非代码文本：** 仍要观察——注释里常藏着 `comment-metadata`（主机名、TODO、版本号）。
- **同一行有多个发现：** 每个不同的观察各出一个点；它们可以共用行号。
