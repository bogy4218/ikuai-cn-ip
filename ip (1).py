import requests
import re
import os
from datetime import datetime, timedelta

def get_data_date():
    """获取当前日期（UTC+0 +1天），用于文件名标记"""
    return (datetime.utcnow() + timedelta(days=1)).strftime("%Y%m%d")

def fetch_domestic_cidrs(url):
    """从指定URL获取国内IPv4 CIDR列表，过滤无效内容"""
    try:
        print("正在下载国内IP列表...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"下载成功，HTTP状态码: {response.status_code}")
        
        # 严格匹配合法 IPv4 CIDR：如 1.2.3.4/24，IP和掩码范围正确
        cidr_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'/([0-9]|[12][0-9]|3[0-2])$'
        )
        cidrs = []
        
        lines = response.text.splitlines()
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if cidr_pattern.match(line):
                cidrs.append(line)
            else:
                print(f"跳过无效行 {line_num}: {line}")
        
        print(f"共提取到 {len(cidrs)} 个有效IPv4网段")
        return cidrs
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return []
    except Exception as e:
        print(f"解析IP列表时出错: {e}")
        return []

def generate_ip_groups(cidrs, data_date):
    """
    生成爱快IP分组文件，每1000个CIDR一组
    group_name 固定为: 国内IP-1, 国内IP-2, ...
    便于ACL长期引用
    """
    group_filename = f"domestic_ikuai_ipgroup-{data_date}.txt"
    
    if os.path.exists(group_filename):
        os.remove(group_filename)
        print(f"已清理旧文件: {group_filename}")
    
    num_line = 1
    num_id = 60  # 建议从60开始，避免与默认规则冲突
    addr_pool = []
    
    with open(group_filename, 'w', encoding='utf-8') as f:
        for cidr in cidrs:
            addr_pool.append(cidr)
            
            if len(addr_pool) < 1000:
                continue
            
            # 写入完整分组（固定名称）
            line = f"id={num_id} comment= type=0 group_name=国内IP-{num_line} addr_pool={','.join(addr_pool)}"
            f.write(line + '\n')
            
            # 重置
            num_id += 1
            num_line += 1
            addr_pool = []
        
        # 写入最后一组剩余网段
        if addr_pool:
            line = f"id={num_id} comment= type=0 group_name=国内IP-{num_line} addr_pool={','.join(addr_pool)}"
            f.write(line + '\n')
            num_line += 1
    
    total_groups = num_line - 1
    print(f"✅ 已生成IP分组文件: {group_filename}")
    print(f"   共 {total_groups} 个分组，命名格式: 国内IP-1 ~ 国内IP-{total_groups}")
    print(f"   使用ID范围: 60 ~ {60 + total_groups - 1}")
    
    return group_filename, total_groups

def main():
    # ================= 配置区 =================
    CN_IP_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/text/cn.txt"
    # ==========================================
    
    data_date = get_data_date()
    print(f"\n🚀 开始处理国内IP列表 | 日期标识: {data_date}\n")
    
    # 1. 获取国内CIDR列表
    cidrs = fetch_domestic_cidrs(CN_IP_URL)
    if not cidrs:
        print("❌ 错误: 未能获取有效的国内IP列表，程序退出")
        return
    
    # 2. 生成IP分组文件（固定名称）
    group_file, num_groups = generate_ip_groups(cidrs, data_date)
    
    if num_groups == 0:
        print("❌ 错误: 未生成任何IP分组，可能IP列表为空")
        return
    
    # ✅ 完成提示
    print("\n" + "="*50)
    print("✅ 所有操作完成！")
    print(f"📄 IP分组文件: {group_file}")
    print(f"📊 总计: {len(cidrs)} 个IP段，分为 {num_groups} 组")
    print(f"💡 使用建议:")
    print(f"   1. 登录爱快路由器，进入【流控分流】->【IP分组】，导入 {group_file}")
    print("="*50)

if __name__ == "__main__":
    main()
