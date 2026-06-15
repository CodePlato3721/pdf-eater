## 单次改动规范(CR规范)

### 颗粒度

每一次改动保持小颗粒度。颗粒度判断标准：

- **同层改动**：单次改动尽量只改同一层。改 service 就不改 router/view；改业务逻辑 py 就不改 REST API 层。
- **一句话概括检验**：本次改动的 CR 中，Design（feature）或 Solution（defect）必须能用一句简短的话概括完。如果需要列多件事才能描述清楚，说明颗粒度太大，应拆分。
- **颗粒度不应过小**：如果本次改动本身就只涉及配置（例如某个 defect 就是配置错误，或本次只改 `PROJECT.md` / `.gitignore`），则配置单独成一个 CR 是合理的。但如果配置改动是为了支撑业务逻辑改动（例如为新功能新增依赖），则依赖变更与源码改动应合并在同一个 CR 里，不应拆开。
- **改动必须闭合**：每次改动都必须有验证手段，保证不会提交错误代码后再修改。验证方式按优先级：
  1. 项目已有对应层的**单元测试** → 随改动一起更新，CR 的 Test Details 写测试摘要。
  2. 项目已有**端到端测试** → 随改动一起更新，CR 的 Test Details 写测试摘要。
  3. 无自动化测试 → 在 CR 的 Test Details 里写清楚**手动验证步骤**，告诉用户执行哪条命令或操作来验证本次改动正确。
  4. 连手动验证都难以做到（例如改动依赖外部环境尚未就绪）→ 在本次改动中附上**临时测试脚手架代码**，CR 注明"下次改动删除脚手架"，下一个 CR 中去除。

### CR（commit request）

每次模型修改完代码**必须**不直接 commit，并且生成一份 CR。
CR 的作用是改动摘要，方便用户及其他 agent 了解改动。
CR 生成后回显给用户，并写入 `.cr.md` 文件。
只包含**项目规则md文件**的改动不用生成CR

**项目规则md文件**: 定义项目规则的.md文件，比如 `PROJECT.md`, `CR.md`, `TASKS.md`。

**CR 回显规则**：回显给用户的 Chat 版本必须与 `.cr.md` 完全一致，包含所有字段，不得省略任何一项。缺少任何字段的 CR 视为不合规。

#### CR 的 reply

CR 创建后等待用户 reply。reply 分为以下几种：
- **approve**：回复"approve, <理由>"。进行**reply 后的 CR 文件操作**。最后执行 commit & push。
- **reject**：回复"reject, <理由>"。回滚所有改动。并进行**reply 后的 CR 文件操作**。
- **remake**：回复"remake"。当 CR 混乱或内容有误时使用。模型基于 `git diff HEAD` 全量 diff 从头生成一份新 CR，覆盖当前 `.cr.md`，回显给用户后继续等待 reply。
- **ask**：用户通过多轮提问了解本次改动的细节，不造成任何代码改动。模型只回答问题，不执行任何操作，不重新生成 CR。用户问完后再做出 approve 或 reject 的决定。
- **modify**：修改。用户可以：1. 自己手动更改并要求模型更新 CR；2. 让模型修改代码，模型自动更新 CR。**更新 CR 时只在现有 `.cr.md` 基础上补充或修正变更内容，不得整体重做**——在受影响的字段（Source Details、Source Tree、Test Result 等）追加或修改对应内容即可。更新后回显给用户并继续等待 reply。只有收到 `remake` 指令时才从头重写 CR。

#### reply 后的 CR 文件操作

approve 或 reject 执行完对应操作后：
- `.cr.md` 中增加 **Reply** 段落，写上reply的结果和理由。可选的结果有 approve, reject
- `.cr.md` 重命名为 `cr.<timestamp>.md`，`timestamp` 格式 `yyyyMMddHHmmss`
- 移入 `cr` 文件夹（不存在则新建）
- `cr` 文件夹会提交到 git；`.cr.md` 已加入 `.gitignore`

#### CR 的格式

CR 分为 feature 和 defect 两种。

**Source Tree** 和 **Test Tree** 必须使用 ASCII 文件树格式，不可以用一句话代替，例如：
```
project/
├── src/
│   └── service.py    ← updated
└── tests/
    └── test_service.py    ← new
```

**feature**
- **Design**：本次改动的设计摘要
- **Source Details**：源码核心细节，1~2 行代码，简短，不含测试改动
- **Source Tree**：本次改动的源码文件树（ASCII 树）
- **Test Details**：测试改动摘要。细节见 **CR 的测试方式**
- **Test Tree**：本次改动的测试文件树（ASCII 树）；细节见 **CR 的测试方式**
- **Test Result**：测试的结果。细节见 **CR 的测试方式**

**defect**
- **Root Cause**：defect 的根本原因
- **Solution**：修改方案摘要
- **Source Details**：源码核心细节，1~2 行代码，简短，不含测试改动
- **Source Tree**：本次改动的源码文件树（ASCII 树）
- **Test Details**：测试改动摘要。细节见 **CR 的测试方式**
- **Test Tree**：本次改动的测试文件树（ASCII 树）；细节见 **CR 的测试方式**
- **Test Result**：测试的结果。细节见 **CR 的测试方式**

#### CR 的测试方式
CR中可选的测试方式有端到端测试，单元测试，无测试。他们有不同的处理方式。
**无测试**
本次改动不需要测试，比如更新 `PROJECT.md` 的文本内容，修改 `.gitignore` 等
- **Test Details**： `无变更`
- **Test Tree**： `无变更`
- **Test Result**： `无变更`

**单元测试**
模型自己在 `tests/unit`下新增，更改单元测试，执行单元测试，将执行结果摘要写入 Test Result（通过/失败条数、失败原因）
- **Test Details**：写出本次单元测试的测试目的，方式的摘要
- **Test Tree**：本次改动的测试文件树（ASCII 树）
- **Test Result**：单元测试的结果

**端到端测试**
模型自己在 `tests/e2e`下新增，更改端到端测试，执行端到端测试，将执行结果摘要写入 Test Result
- **Test Details**：写出本次单元测试的测试目的，方式的摘要
- **Test Tree**：本次改动的测试文件树（ASCII 树）
- **Test Result**：端到端测试的结果
