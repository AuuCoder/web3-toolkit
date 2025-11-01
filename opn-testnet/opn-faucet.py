from common.config_loader import ConfigLoader
import os
import requests  # pyright: ignore[reportMissingModuleSource]
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pynocaptcha import ReCaptchaUniversalCracker, ReCaptchaEnterpriseCracker, ReCaptchaSteamCracker  # pyright: ignore[reportMissingImports]
from eth_account import Account  # pyright: ignore[reportMissingImports]

# 指定当前项目目录
current_dir = os.path.dirname(os.path.abspath(__file__))

config = ConfigLoader(current_dir)\
            .load_env(keys=['USER_TOKEN', 'PROXY_API', 'MAX_WORKERS'])

USER_TOKEN = config.get('USER_TOKEN')
PROXY_API = config.get('PROXY_API')
MAX_WORKERS = int(config.get('MAX_WORKERS', 5))  # 默认5个线程

# 读取私钥列表
wallet_file = os.path.join(current_dir, 'wallet.json')
with open(wallet_file, 'r', encoding='utf-8') as f:
    private_keys = json.load(f)

# 将私钥转换为钱包地址
wallet_addresses = []
print("🔐 开始转换私钥为地址...")
for idx, private_key in enumerate(private_keys, 1):
    try:
        # 确保私钥格式正确（添加 0x 前缀如果没有的话）
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        # 从私钥生成账户
        account = Account.from_key(private_key)
        wallet_addresses.append({
            'private_key': private_key,
            'address': account.address
        })
        print(f"  [{idx}] {account.address}")
    except Exception as e:
        print(f"  [{idx}] ❌ 私钥转换失败: {str(e)}")
        continue

print(f"\n📋 成功转换 {len(wallet_addresses)} 个钱包地址")
print(f"🧵 线程数: {MAX_WORKERS}")
print("=" * 60)

# 统计信息
success_count = 0
failed_count = 0
already_claimed_count = 0
results = []

# 线程锁，用于保护共享变量
stats_lock = threading.Lock()
results_lock = threading.Lock()
print_lock = threading.Lock()

def thread_print(msg):
    """线程安全的打印函数"""
    with print_lock:
        print(msg)

def get_proxy_ip(silent=False):
    """从API获取代理IP"""
    if not PROXY_API:
        if not silent:
            thread_print("⚠️ 未配置 PROXY_API，将不使用代理")
        return None
    
    try:
        response = requests.get(PROXY_API, timeout=10)
        if response.status_code == 200:
            proxy_str = response.text.strip()
            if not silent:
                thread_print(f"🌐 获取到代理IP: {proxy_str}")
            # 返回格式: 38.55.17.118:54055
            return {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }
        else:
            if not silent:
                thread_print(f"⚠️ 获取代理IP失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        if not silent:
            thread_print(f"⚠️ 获取代理IP异常: {str(e)}")
        return None

def get_captcha_token():
    """获取验证码token"""
    cracker = ReCaptchaUniversalCracker(
        user_token=USER_TOKEN,
        sitekey="6Ld1uvorAAAAAKwGWoEHDYIq_yo3dSvshmNQ9ykF",
        referer="https://faucet.iopn.tech",
        size="normal",
        title="OPN Chain Faucet",
    )
    ret = cracker.crack()
    return ret.get('token')

def claim_faucet(wallet_address, captcha_token, proxies=None):
    """领取水龙头"""
    url = "https://faucet.iopn.tech/api/faucet/claim"
    
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "Referer": "https://faucet.iopn.tech/"
    }
    
    payload = {
        "address": wallet_address,
        "captchaToken": captcha_token
    }
    
    response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)
    return response

def process_wallet(idx, wallet_info, total):
    """处理单个钱包的领取任务"""
    global success_count, failed_count, already_claimed_count
    
    wallet_address = wallet_info['address']
    thread_print(f"\n[{idx}/{total}] 🚀 开始处理: {wallet_address}")
    
    max_retries = 3
    claim_success = False
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                thread_print(f"[{idx}/{total}] 🔄 第 {attempt} 次重试...")
                time.sleep(2)  # 重试前等待2秒
            
            # 获取代理IP
            thread_print(f"[{idx}/{total}] 🔄 获取代理IP...")
            proxies = get_proxy_ip(silent=True)
            if proxies:
                thread_print(f"[{idx}/{total}] ✅ 代理IP设置成功")
            else:
                thread_print(f"[{idx}/{total}] ⚠️  将直接连接")
            
            # 获取验证码
            thread_print(f"[{idx}/{total}] 🔄 获取验证码...")
            captcha_token = get_captcha_token()
            thread_print(f"[{idx}/{total}] ✅ 验证码获取成功")
            
            # 领取水龙头
            thread_print(f"[{idx}/{total}] 🔄 发送领取请求...")
            response = claim_faucet(wallet_address, captcha_token, proxies)
            
            thread_print(f"[{idx}/{total}] 📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                thread_print(f"[{idx}/{total}] ✅ 领取成功! {wallet_address}")
                
                with stats_lock:
                    success_count += 1
                with results_lock:
                    results.append({
                        "address": wallet_address,
                        "private_key": wallet_info['private_key'],
                        "status": "success",
                        "attempts": attempt,
                        "response": result
                    })
                claim_success = True
                break  # 成功后跳出重试循环
            else:
                thread_print(f"[{idx}/{total}] ❌ 领取失败! 状态码: {response.status_code}")
                thread_print(f"[{idx}/{total}] 📝 响应内容: {response.text}")
                
                # 检查是否是已经领取过的错误
                if "This address has already claimed recently" in response.text:
                    thread_print(f"[{idx}/{total}] ⏭️  该地址最近已经领取过，跳过重试")
                    
                    with stats_lock:
                        already_claimed_count += 1
                    with results_lock:
                        results.append({
                            "address": wallet_address,
                            "private_key": wallet_info['private_key'],
                            "status": "already_claimed",
                            "attempts": attempt,
                            "response": response.text
                        })
                    claim_success = True  # 标记为已处理，跳出重试循环
                    break
                
                # 如果还有重试机会，不记录失败
                if attempt < max_retries:
                    thread_print(f"[{idx}/{total}] ⏳ 将重试...")
                else:
                    thread_print(f"[{idx}/{total}] ❌ 已达到最大重试次数，放弃该地址")
                    
                    with stats_lock:
                        failed_count += 1
                    with results_lock:
                        results.append({
                            "address": wallet_address,
                            "private_key": wallet_info['private_key'],
                            "status": "failed",
                            "attempts": attempt,
                            "response": response.text
                        })
                
        except Exception as e:
            thread_print(f"[{idx}/{total}] ❌ 请求异常: {str(e)}")
            
            # 如果还有重试机会，不记录失败
            if attempt < max_retries:
                thread_print(f"[{idx}/{total}] ⏳ 将重试...")
            else:
                thread_print(f"[{idx}/{total}] ❌ 已达到最大重试次数，放弃该地址")
                
                with stats_lock:
                    failed_count += 1
                with results_lock:
                    results.append({
                        "address": wallet_address,
                        "private_key": wallet_info['private_key'],
                        "status": "error",
                        "attempts": attempt,
                        "error": str(e)
                    })
    
    return wallet_address

# 使用线程池处理所有钱包
print("\n🚀 开始批量处理钱包...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # 提交所有任务
    futures = {
        executor.submit(process_wallet, idx, wallet_info, len(wallet_addresses)): (idx, wallet_info) 
        for idx, wallet_info in enumerate(wallet_addresses, 1)
    }
    
    # 等待所有任务完成
    completed = 0
    for future in as_completed(futures):
        completed += 1
        try:
            wallet_address = future.result()
            thread_print(f"\n✅ 进度: {completed}/{len(wallet_addresses)} 已完成")
        except Exception as e:
            thread_print(f"\n❌ 任务执行异常: {str(e)}")

end_time = time.time()
elapsed_time = end_time - start_time

# 输出统计信息
print("\n" + "=" * 60)
print("📊 执行完成！统计信息：")
print("=" * 60)
print(f"✅ 成功: {success_count} 个")
print(f"⏭️  已领取过: {already_claimed_count} 个")
print(f"❌ 失败: {failed_count} 个")
print(f"📝 总计: {len(wallet_addresses)} 个")
print(f"⏱️  总耗时: {elapsed_time:.2f} 秒")
print(f"🧵 使用线程数: {MAX_WORKERS}")
print(f"⚡ 平均速度: {elapsed_time/len(wallet_addresses):.2f} 秒/个")

# 保存结果到文件
result_file = os.path.join(current_dir, 'claim_results.json')
with open(result_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(wallet_addresses),
        "success": success_count,
        "already_claimed": already_claimed_count,
        "failed": failed_count,
        "details": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 详细结果已保存到: {result_file}")
