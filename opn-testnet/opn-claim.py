"""
OPN 测试网 Claim 操作脚本

功能：
- 批量读取私钥
- 连接 OPN 测试网
- 调用合约执行 claim 操作
- 自动重试机制（最多3次）
- 保存执行结果
"""

import os
import json
import time
from web3 import Web3  # pyright: ignore[reportMissingImports]
from eth_account import Account  # pyright: ignore[reportMissingImports]

# OPN 测试网配置
RPC_URL = "https://testnet-rpc.iopn.tech"
CHAIN_ID = 984
EXPLORER_URL = "https://testnet.iopn.tech"
CONTRACT_ADDRESS = "0xbc5c49abc5282994bd2c641438391d5e2e730c25"
CLAIM_DATA = "0x4e71d92d"

# 指定当前项目目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 连接到 OPN 测试网
print("🔗 连接到 OPN 测试网...")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if w3.is_connected():
    print(f"✅ 已连接到 OPN 测试网")
    print(f"📊 当前区块高度: {w3.eth.block_number}")
else:
    print("❌ 无法连接到 OPN 测试网")
    exit(1)

# 读取私钥列表
wallet_file = os.path.join(current_dir, 'wallet.json')
with open(wallet_file, 'r', encoding='utf-8') as f:
    private_keys = json.load(f)

# 将私钥转换为账户
accounts = []
print("\n🔐 开始加载钱包...")
for idx, private_key in enumerate(private_keys, 1):
    try:
        # 确保私钥格式正确
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        account = Account.from_key(private_key)
        
        # 查询余额
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        accounts.append({
            'private_key': private_key,
            'address': account.address,
            'balance': balance_eth
        })
        print(f"  [{idx}] {account.address} (余额: {balance_eth:.6f} OPN)")
    except Exception as e:
        print(f"  [{idx}] ❌ 加载失败: {str(e)}")
        continue

print(f"\n📋 成功加载 {len(accounts)} 个钱包")
print("=" * 70)

# 统计信息
success_count = 0
failed_count = 0
results = []


def execute_claim(account_info, attempt=1):
    """
    执行 claim 操作
    
    Args:
        account_info: 账户信息
        attempt: 当前尝试次数
    
    Returns:
        (success, tx_hash, error_msg)
    """
    try:
        private_key = account_info['private_key']
        address = account_info['address']
        
        # 创建账户对象
        account = Account.from_key(private_key)
        
        # 获取 nonce
        nonce = w3.eth.get_transaction_count(address)
        
        # 获取 gas price
        gas_price = w3.eth.gas_price
        
        # 构建交易
        transaction = {
            'from': address,
            'to': Web3.to_checksum_address(CONTRACT_ADDRESS),
            'value': 0,
            'gas': 200000,  # 预估 gas limit
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'data': CLAIM_DATA
        }
        
        # 估算实际需要的 gas
        try:
            estimated_gas = w3.eth.estimate_gas(transaction)
            transaction['gas'] = int(estimated_gas * 1.2)  # 增加 20% 作为缓冲
        except Exception as e:
            print(f"    ⚠️  Gas 估算失败，使用默认值: {str(e)}")
        
        # 签名交易
        signed_txn = account.sign_transaction(transaction)
        
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"    📤 交易已发送: {tx_hash_hex}")
        print(f"    🔍 查看交易: {EXPLORER_URL}/tx/{tx_hash_hex}")
        
        # 等待交易确认
        print(f"    ⏳ 等待交易确认...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            return True, tx_hash_hex, None
        else:
            return False, tx_hash_hex, "交易执行失败"
            
    except Exception as e:
        return False, None, str(e)


# 遍历所有账户
for idx, account_info in enumerate(accounts, 1):
    address = account_info['address']
    balance = account_info['balance']
    
    print(f"\n[{idx}/{len(accounts)}] 处理钱包: {address}")
    print(f"    💰 余额: {balance:.6f} OPN")
    print("-" * 70)
    
    # 检查余额是否足够
    if balance < 0.0001:
        print(f"    ❌ 余额不足，跳过")
        failed_count += 1
        results.append({
            "address": address,
            "private_key": account_info['private_key'],
            "status": "failed",
            "error": "余额不足"
        })
        continue
    
    max_retries = 3
    claim_success = False
    
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"\n    🔄 第 {attempt} 次重试...")
            time.sleep(3)  # 重试前等待3秒
        
        print(f"    🔄 执行 claim 操作...")
        success, tx_hash, error_msg = execute_claim(account_info, attempt)
        
        if success:
            print(f"    ✅ Claim 成功!")
            print(f"    📝 交易哈希: {tx_hash}")
            success_count += 1
            results.append({
                "address": address,
                "private_key": account_info['private_key'],
                "status": "success",
                "attempts": attempt,
                "tx_hash": tx_hash,
                "explorer_url": f"{EXPLORER_URL}/tx/{tx_hash}"
            })
            claim_success = True
            break
        else:
            print(f"    ❌ Claim 失败: {error_msg}")
            
            if attempt < max_retries:
                print(f"    ⏳ 将在 {max_retries - attempt} 次机会中重试...")
            else:
                print(f"    ❌ 已达到最大重试次数 ({max_retries} 次)，放弃该地址")
                failed_count += 1
                results.append({
                    "address": address,
                    "private_key": account_info['private_key'],
                    "status": "failed",
                    "attempts": attempt,
                    "error": error_msg,
                    "tx_hash": tx_hash if tx_hash else None
                })
    
    # 如果不是最后一个地址，等待一段时间避免请求过快
    if idx < len(accounts):
        wait_time = 5
        print(f"\n    ⏳ 等待 {wait_time} 秒后处理下一个地址...")
        time.sleep(wait_time)

# 输出统计信息
print("\n" + "=" * 70)
print("📊 执行完成！统计信息：")
print("=" * 70)
print(f"✅ 成功: {success_count} 个")
print(f"❌ 失败: {failed_count} 个")
print(f"📝 总计: {len(accounts)} 个")

# 保存结果到文件
result_file = os.path.join(current_dir, 'claim_results.json')
with open(result_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "network": "OPN Testnet",
        "chain_id": CHAIN_ID,
        "contract": CONTRACT_ADDRESS,
        "total": len(accounts),
        "success": success_count,
        "failed": failed_count,
        "details": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 详细结果已保存到: {result_file}")
print(f"🔍 区块浏览器: {EXPLORER_URL}")

