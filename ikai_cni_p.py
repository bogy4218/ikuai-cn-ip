import requests
import re
import os

def fetch_domestic_cidrs(url):
    """获取并过滤国内IPv4 CIDR列表"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 匹配有效IPv4 CIDR格式
        cidr_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'/([0-9]|[12][0-9]|3[0-2])$'
        )
        cidrs = []
        
        for line in response.text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and cidr_pattern.match(line):
                cidrs.append(line)
        
        return cidrs if cidrs else None
        
    except Exception:
        return None

def generate_ip_group_file(cidrs):
    """生成固定名称为ikuai_cn_ipgroup.txt的文件"""
    filename = "ikuai_cn_ipgroup.txt"
    
    # 清除旧文件
    if os.path.exists(filename):
        os.remove(filename)
    
    num_id = 60  # 起始ID
    group_num = 1
    addr_pool = []
    
    with open(filename, 'w', encoding='utf-8') as f:
        for cidr in cidrs:
            addr_pool.append(cidr)
            
            # 每1000个IP段分一组
            if len(addr_pool) >= 1000:
                f.write(f"id={num_id} comment= type=0 group_name=国内IP-{group_num} addr_pool={','.join(addr_pool)}\n")
                num_id += 1
                group_num += 1
                addr_pool = []
        
        # 处理剩余IP段
        if addr_pool:
            f.write(f"id={num_id} comment= type=0 group_name=国内IP-{group_num} addr_pool={','.join(addr_pool)}\n")
    
    return filename

def main():
    # 国内IP列表来源
    CN_IP_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/text/cn.txt"
    
    # 获取IP列表
    cidrs = fetch_domestic_cidrs(CN_IP_URL)
    if not cidrs:
        return  # 出错时直接退出
    
    # 生成文件
    generate_ip_group_file(cidrs)

if __name__ == "__main__":
    main()
