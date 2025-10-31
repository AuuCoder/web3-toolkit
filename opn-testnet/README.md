# OPN Testnet 工具集

OPN 测试网自动化工具集合，包含水龙头领取和链上 Claim 操作。

## 工具列表

### 1. opn-faucet.py - 水龙头自动领取

自动破解验证码并领取测试币。

**功能特性**：

- 🔐 自动从私钥生成 EVM 钱包地址
- 🤖 自动破解 reCAPTCHA 验证码
- 💧 批量领取多个钱包地址
- 🔄 智能重试机制（失败自动重试最多 3 次）
- 📝 详细的日志输出和进度显示
- 💾 自动保存领取结果

### 2. opn-claim.py - 链上 Claim 操作

在 OPN 测试网上执行合约 claim 操作。

**功能特性**：

- ⛓️ 连接 OPN 测试网 RPC
- 🔐 批量处理多个钱包
- 💰 自动检查余额
- 📤 执行合约交易
- 🔄 智能重试机制（最多 3 次）
- 🔍 自动生成区块浏览器链接
- 💾 保存交易结果

**网络信息**：

- RPC: https://testnet-rpc.iopn.tech
- Chain ID: 984
- 区块浏览器: https://testnet.iopn.tech
- Claim 合约: 0xbc5c49abc5282994bd2c641438391d5e2e730c25

## 环境要求

- Python 3.7+
- 有效的 nocaptcha.io 账户和 TOKEN（仅 opn-faucet.py 需要）
- OPN 测试网代币（仅 opn-claim.py 需要，用于 gas 费）

## 安装步骤

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量：

```bash
cp .env.example .env
```

3. 编辑 `.env` 文件，填入您的 USER_TOKEN：

```bash
# 从 https://www.nocaptcha.io/register?c=P4QdvE 获取的 USER_TOKEN
USER_TOKEN=your_nocaptcha_token
```

4. 配置钱包私钥：

```bash
cp wallet.json.example wallet.json
```

编辑 `wallet.json`，添加您的钱包私钥（支持带或不带 0x 前缀）：

```json
["your_private_key_1", "0xyour_private_key_2", "your_private_key_3"]
```

⚠️ **重要**：`wallet.json` 存放的是**私钥**，不是地址！脚本会自动将私钥转换为 EVM 地址。

## 使用方法

### 方法 1：水龙头领取（opn-faucet.py）

用于从水龙头领取测试币：

```bash
python opn-faucet.py
```

脚本会自动：

- 🔐 读取 `wallet.json` 中的所有私钥并转换为地址
- 🔄 为每个地址获取验证码并领取水龙头
- 🔁 失败自动重试（最多 3 次，每次间隔 2 秒）
- 📊 显示实时进度和统计信息
- 💾 保存详细结果到 `claim_results.json`（包含私钥和地址对应关系）

执行示例输出：

```
🔐 开始转换私钥为地址...
  [1] 0x1234************************************5678
  [2] 0xabcd************************************abcd
  [3] 0x9876************************************3210

📋 成功转换 3 个钱包地址
============================================================

[1/3] 处理钱包: 0x1234************************************5678
------------------------------------------------------------
🔄 获取验证码...
✅ 验证码获取成功: 0cAFcWeA6HkzdpEikKYdV6qdlmSAVI2fvBjrFnFo0zV8uJzLN...
🔄 发送领取请求...
📊 响应状态码: 200
✅ 领取成功!

⏳ 等待 3 秒后处理下一个地址...

[2/3] 处理钱包: 0xabcd************************************abcd
------------------------------------------------------------
🔄 获取验证码...
✅ 验证码获取成功: 0cAFcWeA6HkzdpEikKYdV6qdlmSAVI2fvBjrFnFo0zV8uJzLN...
🔄 发送领取请求...
📊 响应状态码: 429
❌ 领取失败! 状态码: 429
⏳ 将在 2 次机会中重试...

🔄 第 2 次重试...
🔄 获取验证码...
✅ 验证码获取成功: ...
🔄 发送领取请求...
📊 响应状态码: 200
✅ 领取成功!

============================================================
📊 执行完成！统计信息：
============================================================
✅ 成功: 2 个
❌ 失败: 1 个
📝 总计: 3 个

💾 详细结果已保存到: claim_results.json
```

### 方法 2：链上 Claim 操作（opn-claim.py）

用于在 OPN 测试网上执行合约 claim 操作：

```bash
python opn-claim.py
```

脚本会自动：

- 🔗 连接到 OPN 测试网
- 🔐 读取 `wallet.json` 中的所有私钥
- 💰 检查每个钱包的余额
- 📤 执行合约 claim 交易
- 🔁 失败自动重试（最多 3 次，每次间隔 3 秒）
- 🔍 生成区块浏览器链接
- 💾 保存详细结果到 `claim_results.json`

执行示例输出：

```
🔗 连接到 OPN 测试网...
✅ 已连接到 OPN 测试网
📊 当前区块高度: 12345

🔐 开始加载钱包...
  [1] 0x1234************************************5678 (余额: 1.234567 OPN)
  [2] 0xabcd************************************abcd (余额: 0.567890 OPN)

📋 成功加载 2 个钱包
======================================================================

[1/2] 处理钱包: 0x1234************************************5678
    💰 余额: 1.234567 OPN
----------------------------------------------------------------------
    🔄 执行 claim 操作...
    📤 交易已发送: 0xabc123...
    🔍 查看交易: https://testnet.iopn.tech/tx/0xabc123...
    ⏳ 等待交易确认...
    ✅ Claim 成功!
    📝 交易哈希: 0xabc123...

    ⏳ 等待 5 秒后处理下一个地址...

======================================================================
📊 执行完成！统计信息：
======================================================================
✅ 成功: 2 个
❌ 失败: 0 个
📝 总计: 2 个

💾 详细结果已保存到: claim_results.json
🔍 区块浏览器: https://testnet.iopn.tech
```

⚠️ **注意**：执行 claim 操作需要钱包有足够的 OPN 代币作为 gas 费。建议先使用 opn-faucet.py 领取测试币。

### 完整工作流程

推荐的完整操作流程：

```bash
# 1. 生成钱包（如果还没有）
cd ../utils
python generate_wallets.py
# 输入数量，生成 wallet.json

# 2. 复制到 opn-testnet 目录
cp wallet.json ../opn-testnet/

# 3. 领取测试币
cd ../opn-testnet
python opn-faucet.py
# 等待完成，钱包将获得测试币

# 4. 执行 claim 操作
python opn-claim.py
# 使用测试币执行链上 claim
```

## 配置说明

### USER_TOKEN

从 [nocaptcha.io](https://www.nocaptcha.io/register?c=P4QdvE) 获取的用户 TOKEN，用于破解 reCAPTCHA。

**使用范围**：仅 opn-faucet.py 需要

### wallet.json

包含需要领取水龙头的钱包**私钥**列表，JSON 数组格式：

```json
["私钥1", "0x私钥2", "私钥3"]
```

⚠️ **注意**：

- 存放的是**私钥**，不是地址
- 私钥可以带或不带 `0x` 前缀
- 脚本会自动将私钥转换为 EVM 地址
- **务必保护好此文件，不要泄露或提交到 Git**

### claim_results.json

脚本执行后自动生成的结果文件，包含详细的执行记录。

**opn-faucet.py 结果格式**：

```json
{
  "timestamp": "2025-10-31 12:34:56",
  "total": 3,
  "success": 2,
  "failed": 1,
  "details": [
    {
      "address": "0x...",
      "private_key": "0x...",
      "status": "success",
      "attempts": 1,
      "response": {...}
    }
  ]
}
```

**opn-claim.py 结果格式**：

```json
{
  "timestamp": "2025-10-31 12:34:56",
  "network": "OPN Testnet",
  "chain_id": 984,
  "contract": "0xbc5c49abc5********************730c25",
  "total": 2,
  "success": 2,
  "failed": 0,
  "details": [
    {
      "address": "0x...",
      "private_key": "0x...",
      "status": "success",
      "attempts": 1,
      "tx_hash": "0xabc123...",
      "explorer_url": "https://testnet.iopn.tech/tx/0xabc123..."
    }
  ]
}
```

- `attempts` 字段表示成功所需的尝试次数（1-3）
- `tx_hash` 字段包含交易哈希（仅 opn-claim.py）
- `explorer_url` 字段包含区块浏览器链接（仅 opn-claim.py）
- ⚠️ **注意**：此文件包含私钥信息，已添加到 `.gitignore`，请妥善保管。

## 注意事项

⚠️ **重要提示**：

- 此工具仅用于测试网环境
- 请勿滥用水龙头服务
- 确保您的 nocaptcha.io 账户有足够的额度（仅 opn-faucet.py）
- **🔒 `wallet.json` 存储的是私钥，务必保护好，不要泄露或提交到 Git**
- **🔒 `claim_results.json` 包含私钥信息，也要妥善保管**
- 保护好您的 `.env` 文件
- 脚本会在每个地址之间自动等待（faucet: 3 秒，claim: 5 秒）
- 失败会自动重试最多 3 次
- 私钥支持带或不带 `0x` 前缀，脚本会自动处理
- opn-claim.py 需要钱包有足够的 OPN 代币作为 gas 费

## OPN 测试网信息

根据 [OPN 测试网浏览器](https://testnet.iopn.tech)：

- **RPC URL**: https://testnet-rpc.iopn.tech
- **Chain ID**: 984
- **区块浏览器**: https://testnet.iopn.tech
- **Claim 合约地址**: 0xbc5c49abc5282994bd2c641438391d5e2e730c25
- **Claim 函数**: 0x4e71d92d

## 常见问题

### 私钥转换失败

- 检查私钥格式是否正确（64 位十六进制字符）
- 确保私钥是有效的 EVM 私钥

### 验证码获取失败

- 检查 USER_TOKEN 是否正确
- 检查 nocaptcha.io 账户是否有足够额度

### 领取失败

- 检查生成的钱包地址是否正确
- 检查是否已经达到领取上限
- 检查网络连接是否正常

## License

MIT
