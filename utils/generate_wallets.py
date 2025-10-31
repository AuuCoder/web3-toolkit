"""
批量生成 EVM 钱包地址脚本

功能：
- 批量生成指定数量的 EVM 钱包
- 保存私钥到 JSON 文件（wallet.json 格式）
- 显示对应的地址信息
"""

import json
import os
from eth_account import Account  # pyright: ignore[reportMissingImports]

def generate_wallets(count=10, output_file="wallet.json"):
    """
    生成指定数量的 EVM 钱包
    
    Args:
        count: 要生成的钱包数量
        output_file: 输出文件路径
    """
    print(f"🔐 开始生成 {count} 个 EVM 钱包...")
    print("=" * 70)
    
    wallets = []
    private_keys = []
    
    # 批量生成钱包
    for i in range(count):
        # 生成新账户
        account = Account.create()
        
        wallets.append({
            'index': i + 1,
            'address': account.address,
            'private_key': account.key.hex()
        })
        
        # 只保存私钥到 JSON 文件
        private_keys.append(account.key.hex())
        
        # 显示生成的地址信息
        print(f"[{i+1:3d}] 地址: {account.address}")
        print(f"      私钥: {account.key.hex()}")
        print("-" * 70)
    
    # 保存私钥到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(private_keys, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print(f"✅ 成功生成 {count} 个钱包！")
    print(f"💾 私钥已保存到: {output_file}")
    print("\n⚠️  重要提醒：")
    print("   - 请妥善保管私钥文件，不要泄露！")
    print("   - 这些是真实的钱包私钥，可以用于任何 EVM 链")
    print("   - 建议备份到安全的地方")
    
    # 额外保存一份详细信息（包含地址和私钥对应关系）
    detail_file = output_file.replace('.json', '_detail.json')
    with open(detail_file, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=2, ensure_ascii=False)
    
    print(f"📋 详细信息（地址+私钥）已保存到: {detail_file}")
    
    return wallets


def main():
    """主函数"""
    print("=" * 70)
    print("  🌟 EVM 钱包批量生成工具 🌟")
    print("=" * 70)
    print()
    
    # 获取用户输入
    try:
        count_input = input("请输入要生成的钱包数量 (默认 10): ").strip()
        count = int(count_input) if count_input else 10
        
        if count <= 0:
            print("❌ 数量必须大于 0")
            return
        
        if count > 1000:
            confirm = input(f"⚠️  您要生成 {count} 个钱包，确认吗？(y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ 已取消")
                return
        
        output_input = input("请输入输出文件名 (默认 wallet.json): ").strip()
        output_file = output_input if output_input else "wallet.json"
        
        # 检查文件是否存在
        if os.path.exists(output_file):
            overwrite = input(f"⚠️  文件 {output_file} 已存在，是否覆盖？(y/n): ").strip().lower()
            if overwrite != 'y':
                print("❌ 已取消")
                return
        
        print()
        
        # 生成钱包
        generate_wallets(count, output_file)
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
    except ValueError:
        print("❌ 请输入有效的数字")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    main()

