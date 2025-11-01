"""
OPN 测试网 Claim 操作脚本

功能：
- 批量读取私钥
- 连接 OPN 测试网
- 调用合约执行 claim 操作
- 多线程并发处理
- 自动重试机制（最多3次）
- 保存执行结果
"""

import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.config_loader import ConfigLoader
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

# 加载配置
config = ConfigLoader(current_dir)\
            .load_env(keys=['MAX_WORKERS'])

MAX_WORKERS = int(config.get('MAX_WORKERS', 3))  # 默认3个线程（claim比较慢）

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
print(f"🧵 线程数: {MAX_WORKERS}")
print("=" * 70)

# 统计信息
success_count = 0
failed_count = 0
results = []

# 线程锁，用于保护共享变量
stats_lock = threading.Lock()
results_lock = threading.Lock()
print_lock = threading.Lock()

def thread_print(msg):
    """线程安全的打印函数"""
    with print_lock:
        print(msg)


def execute_claim(account_info, idx, total, attempt=1):
    """
    执行 claim 操作
    
    Args:
        account_info: 账户信息
        idx: 钱包编号
        total: 总钱包数
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
            thread_print(f"[{idx}/{total}] ⚠️  Gas 估算失败，使用默认值: {str(e)}")
        
        # 签名交易
        signed_txn = account.sign_transaction(transaction)
        
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        thread_print(f"[{idx}/{total}] 📤 交易已发送: {tx_hash_hex}")
        thread_print(f"[{idx}/{total}] 🔍 查看交易: {EXPLORER_URL}/tx/{tx_hash_hex}")
        
        # 等待交易确认
        thread_print(f"[{idx}/{total}] ⏳ 等待交易确认...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            return True, tx_hash_hex, None
        else:
            return False, tx_hash_hex, "交易执行失败"
            
    except Exception as e:
        return False, None, str(e)


def process_account(idx, account_info, total):
    """处理单个账户的claim任务"""
    global success_count, failed_count
    
    address = account_info['address']
    balance = account_info['balance']
    
    thread_print(f"\n[{idx}/{total}] 🚀 开始处理: {address}")
    thread_print(f"[{idx}/{total}] 💰 余额: {balance:.6f} OPN")
    
    # 检查余额是否足够
    if balance < 0.0001:
        thread_print(f"[{idx}/{total}] ❌ 余额不足，跳过")
        with stats_lock:
            failed_count += 1
        with results_lock:
            results.append({
                "address": address,
                "private_key": account_info['private_key'],
                "status": "failed",
                "error": "余额不足"
            })
        return address
    
    max_retries = 3
    claim_success = False
    
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            thread_print(f"[{idx}/{total}] 🔄 第 {attempt} 次重试...")
            time.sleep(3)  # 重试前等待3秒
        
        thread_print(f"[{idx}/{total}] 🔄 执行 claim 操作...")
        success, tx_hash, error_msg = execute_claim(account_info, idx, total, attempt)
        
        if success:
            thread_print(f"[{idx}/{total}] ✅ Claim 成功! {address}")
            thread_print(f"[{idx}/{total}] 📝 交易哈希: {tx_hash}")
            
            with stats_lock:
                success_count += 1
            with results_lock:
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
            thread_print(f"[{idx}/{total}] ❌ Claim 失败: {error_msg}")
            
            if attempt < max_retries:
                thread_print(f"[{idx}/{total}] ⏳ 将重试...")
            else:
                thread_print(f"[{idx}/{total}] ❌ 已达到最大重试次数，放弃该地址")
                
                with stats_lock:
                    failed_count += 1
                with results_lock:
                    results.append({
                        "address": address,
                        "private_key": account_info['private_key'],
                        "status": "failed",
                        "attempts": attempt,
                        "error": error_msg,
                        "tx_hash": tx_hash if tx_hash else None
                    })
    
    return address

# 使用线程池处理所有账户
print("\n🚀 开始批量处理账户...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # 提交所有任务
    futures = {
        executor.submit(process_account, idx, account_info, len(accounts)): (idx, account_info) 
        for idx, account_info in enumerate(accounts, 1)
    }
    
    # 等待所有任务完成
    completed = 0
    for future in as_completed(futures):
        completed += 1
        try:
            address = future.result()
            thread_print(f"\n✅ 进度: {completed}/{len(accounts)} 已完成")
        except Exception as e:
            thread_print(f"\n❌ 任务执行异常: {str(e)}")

end_time = time.time()
elapsed_time = end_time - start_time

# 输出统计信息
print("\n" + "=" * 70)
print("📊 执行完成！统计信息：")
print("=" * 70)
print(f"✅ 成功: {success_count} 个")
print(f"❌ 失败: {failed_count} 个")
print(f"📝 总计: {len(accounts)} 个")
print(f"⏱️  总耗时: {elapsed_time:.2f} 秒")
print(f"🧵 使用线程数: {MAX_WORKERS}")
if len(accounts) > 0:
    print(f"⚡ 平均速度: {elapsed_time/len(accounts):.2f} 秒/个")

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

