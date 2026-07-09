## 单次改动规范(CR规范)

### 颗粒度

每一次改动保持小颗粒度。颗粒度判断标准：

- **同层改动**：单次改动尽量只改同一层。改 service 就不改 router/view；改业务逻辑 py 就不改 REST API 层。
- **一句话概括检验**：本次改动的 CR 中，Design（feature）或 Solution（defect）必须能用一句简短的话概括完。如果需要列多件事才能描述清楚，说明颗粒度太大，应拆分。
- **颗粒度不应过小**：如果本次改动本身就只涉及配置（例如某个 defect 就是配置错误，则配置单独成一个 CR 是合理的。但如果配置改动是为了支撑业务逻辑改动（例如为新功能新增依赖），则依赖变更与源码改动应合并在同一个 CR 里，不应拆开。
- **改动必须闭合**：每次改动都必须有验证手段，保证不会提交错误代码后再修改。验证方式按优先级：
  1. 项目已有对应层的**单元测试** → 随改动一起更新，CR 的 Test Details 写测试摘要。
  2. 项目已有**端到端测试** → 随改动一起更新，CR 的 Test Details 写测试摘要。
  3. 无自动化测试 → 在 CR 的 Test Details 里写清楚**手动验证步骤**，告诉用户执行哪条命令或操作来验证本次改动正确。
  4. 连手动验证都难以做到（例如改动依赖外部环境尚未就绪）→ 在本次改动中附上**临时测试脚手架代码**，CR 注明"下次改动删除脚手架"，下一个 CR 中去除。

### CR 的格式

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
- **New Rules**（可选）：格式 `<rule file>: <rule text>`，一行一条。approve 后追加到 `${ROLE_ROOT}/rules/<rule file>`。无新规则时留空

**defect**
- **Root Cause**：defect 的根本原因
- **Solution**：修改方案摘要
- **Source Details**：源码核心细节，1~2 行代码，简短，不含测试改动
- **Source Tree**：本次改动的源码文件树（ASCII 树）
- **Test Details**：测试改动摘要。细节见 **CR 的测试方式**
- **Test Tree**：本次改动的测试文件树（ASCII 树）；细节见 **CR 的测试方式**
- **Test Result**：测试的结果。细节见 **CR 的测试方式**
- **New Rules**（可选）：格式 `<rule file>: <rule text>`，一行一条。approve 后追加到 `${ROLE_ROOT}/rules/<rule file>`。无新规则时留空

### CR 的测试方式
CR 中可选的测试方式有单元测试、端到端测试、人工测试。他们有不同的处理方式。

**单元测试**
模型在 `plato-workspace/tickets/<ticket-number>/status.json` 的 `unit-test-path` 指定的目录下新增、更改单元测试，执行单元测试，将执行结果摘要写入 Test Result（通过/失败条数、失败原因）
- **Test Details**：写出本次单元测试的测试目的、方式的摘要
- **Test Tree**：本次改动的测试文件树（ASCII 树）
- **Test Result**：单元测试的结果

**端到端测试**
模型在 `plato-workspace/tickets/<ticket-number>/status.json` 的 `e2e-test-path` 指定的目录下新增、更改端到端测试，执行端到端测试，将执行结果摘要写入 Test Result
- **Test Details**：写出本次端到端测试的测试目的、方式的摘要
- **Test Tree**：本次改动的测试文件树（ASCII 树）
- **Test Result**：端到端测试的结果

**人工测试**
无法用自动化测试覆盖时，写清楚如何手动测试本次改动：需要执行的命令，或需要启动什么服务、打开浏览器访问什么地址、看到什么结果才算成功
- **Test Details**：手动测试的步骤说明（命令，或启动服务 + 访问地址 + 成功标准）
- **Test Tree**： `无变更`
- **Test Result**：`待人工验证，见 Test Details`
