from common.config_loader import ConfigLoader
import os
import requests  # pyright: ignore[reportMissingModuleSource]
import json
import time
from pynocaptcha import ReCaptchaUniversalCracker, ReCaptchaEnterpriseCracker, ReCaptchaSteamCracker  # pyright: ignore[reportMissingImports]
from eth_account import Account  # pyright: ignore[reportMissingImports]

# 指定当前项目目录
current_dir = os.path.dirname(os.path.abspath(__file__))

config = ConfigLoader(current_dir)\
            .load_env(keys=['USER_TOKEN'])

USER_TOKEN = config.get('USER_TOKEN')

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
print("=" * 60)

# 统计信息
success_count = 0
failed_count = 0
results = []

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

def claim_faucet(wallet_address, captcha_token):
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
    
    response = requests.post(url, headers=headers, json=payload)
    return response

# 遍历所有钱包地址
for idx, wallet_info in enumerate(wallet_addresses, 1):
    wallet_address = wallet_info['address']
    print(f"\n[{idx}/{len(wallet_addresses)}] 处理钱包: {wallet_address}")
    print("-" * 60)
    
    max_retries = 3
    claim_success = False
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"\n🔄 第 {attempt} 次重试...")
                time.sleep(2)  # 重试前等待2秒
            
            # 获取验证码
            print("🔄 获取验证码...")
            captcha_token = get_captcha_token()
            print(f"✅ 验证码获取成功: {captcha_token[:50]}...")
            
            # 领取水龙头
            print("🔄 发送领取请求...")
            response = claim_faucet(wallet_address, captcha_token)
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 领取成功!")
                print(f"📝 响应内容: {json.dumps(result, ensure_ascii=False)}")
                success_count += 1
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
                print(f"❌ 领取失败! 状态码: {response.status_code}")
                print(f"📝 响应内容: {response.text}")
                
                # 如果还有重试机会，不记录失败
                if attempt < max_retries:
                    print(f"⏳ 将在 {max_retries - attempt} 次机会中重试...")
                else:
                    print(f"❌ 已达到最大重试次数 ({max_retries} 次)，放弃该地址")
                    failed_count += 1
                    results.append({
                        "address": wallet_address,
                        "private_key": wallet_info['private_key'],
                        "status": "failed",
                        "attempts": attempt,
                        "response": response.text
                    })
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            
            # 如果还有重试机会，不记录失败
            if attempt < max_retries:
                print(f"⏳ 将在 {max_retries - attempt} 次机会中重试...")
            else:
                print(f"❌ 已达到最大重试次数 ({max_retries} 次)，放弃该地址")
                failed_count += 1
                results.append({
                    "address": wallet_address,
                    "private_key": wallet_info['private_key'],
                    "status": "error",
                    "attempts": attempt,
                    "error": str(e)
                })
    
    # 如果不是最后一个地址，等待一段时间避免请求过快
    if idx < len(wallet_addresses):
        wait_time = 3
        print(f"\n⏳ 等待 {wait_time} 秒后处理下一个地址...")
        time.sleep(wait_time)

# 输出统计信息
print("\n" + "=" * 60)
print("📊 执行完成！统计信息：")
print("=" * 60)
print(f"✅ 成功: {success_count} 个")
print(f"❌ 失败: {failed_count} 个")
print(f"📝 总计: {len(wallet_addresses)} 个")

# 保存结果到文件
result_file = os.path.join(current_dir, 'claim_results.json')
with open(result_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(wallet_addresses),
        "success": success_count,
        "failed": failed_count,
        "details": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 详细结果已保存到: {result_file}")
