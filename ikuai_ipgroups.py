import requests
import re
import os
from datetime import datetime

# -------------------------- 核心配置参数 --------------------------
# IPv6配置
IPV6_SOURCES = [
    "https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest",
    "https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chn_ip_v6.txt"
]
IPV6_OUTPUT_FILE = "ikuai_cn_ipv6group.txt"
IPV6_START_ID = 70
IPV6_BASE_GROUP_NAME = "国内IPv6"

# IPv4配置
IPV4_SOURCES = [
    "https://metowolf.github.io/iplist/data/special/china.txt",
    "https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/text/cn.txt"
]
IPV4_OUTPUT_FILE = "ikuai_cn_ipv4group.txt"
IPV4_START_ID = 60  # IPv4从60开始
IPV4_BASE_GROUP_NAME = "国内IPv4"

# 公共配置
RECORDS_PER_ID = 1000
# ------------------------------------------------------------------


def fetch_ip_data(url):
    """获取IP地址段原始数据（兼容IPv4和IPv6）"""
    try:
        print(f"[+] 正在获取数据源：{url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"[-] 获取 {url} 失败：{str(e)}")
        return None


def parse_apnic_data(raw_data):
    """解析APNIC格式的IPv6数据"""
    ipv6_cidr_list = []
    if not raw_data:
        return ipv6_cidr_list
    for line in raw_data.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split("|")
            if len(parts) >= 7 and parts[1] == "CN" and parts[2] == "ipv6":
                ipv6_cidr_list.append(f"{parts[3]}/{parts[4]}".lower())
    return ipv6_cidr_list


def parse_ipv6_cidr(raw_data):
    """解析纯IPv6 CIDR格式数据"""
    ipv6_pattern = re.compile(r"^[0-9a-fA-F:]+/\d{1,3}$")
    return [line.strip().lower() for line in raw_data.split("\n") 
            if line.strip() and not line.startswith("#") and ipv6_pattern.match(line.strip())]


def get_cidrs_from_response(response):
    """从响应文本中提取有效的IPv4 CIDR地址"""
    if not response:
        return []
        
    # 匹配有效IPv4 CIDR格式的正则表达式
    cidr_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r'/([0-9]|[12][0-9]|3[0-2])$'
    )
    cidrs = []
    
    for line in response.text.splitlines():
        line = line.strip()
        # 跳过空行和注释行，匹配有效的CIDR
        if line and not line.startswith('#') and cidr_pattern.match(line):
            cidrs.append(line)
    
    return cidrs


def clean_ip_data(ip_list):
    """清洗IP地址段：去重+排序"""
    unique_sorted = sorted(list(set(ip_list)))
    print(f"[+] 数据清洗完成：{len(ip_list)}条原始 → {len(unique_sorted)}条去重")
    return unique_sorted


def split_into_chunks(lst, chunk_size=RECORDS_PER_ID):
    """拆分列表为固定大小的块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def generate_ikuai_records(ip_chunks, start_id, base_group_name):
    """生成爱快格式记录 - 修复了注释中包含%20的问题"""
    records = []
    current_id = start_id
    for index, chunk in enumerate(ip_chunks):
        group_name = f"{base_group_name}-{index + 1}"
        # 修复：使用普通空格代替%20编码
        comment = ", ".join(chunk)
        addr_pool = ",".join([cidr.split("/")[0] for cidr in chunk])
        records.append(f"id={current_id} comment={comment} group_name={group_name} addr_pool={addr_pool}")
        current_id += 1
    return records


def save_to_local(records, filename, start_id, base_group_name):
    """保存到本地文件并显示统计信息"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(records))
        
        total = sum(len(record.split("comment=")[1].split(", ")) for record in records)
        print(f"\n[✅] 文件生成成功：{os.path.abspath(filename)}")
        print(f"[📊] 统计：{len(records)}条记录 | ID范围：{start_id}~{start_id + len(records) - 1}")
        print(f"[📊] 组名：{base_group_name}-1~{base_group_name}-{len(records)} | 总地址段：{total}")
    except Exception as e:
        print(f"[-] 保存失败：{str(e)}")


def process_ipv6():
    """处理IPv6地址段"""
    print("\n" + "-" * 50)
    print("开始处理IPv6地址段...")
    all_ipv6 = []
    for source in IPV6_SOURCES:
        response = fetch_ip_data(source)
        if not response:
            continue
            
        raw_data = response.text
        parsed = parse_apnic_data(raw_data) if "apnic.net" in source else parse_ipv6_cidr(raw_data)
        all_ipv6.extend(parsed)
        print(f"[+] 从 {source} 解析到 {len(parsed)} 条IPv6")

    if not all_ipv6:
        print("\n[❌] 未获取到有效IPv6地址段")
        return
        
    clean_ipv6 = clean_ip_data(all_ipv6)
    ipv6_chunks = split_into_chunks(clean_ipv6)
    print(f"[+] IPv6分块完成：{len(ipv6_chunks)}个块")
    records = generate_ikuai_records(ipv6_chunks, IPV6_START_ID, IPV6_BASE_GROUP_NAME)
    save_to_local(records, IPV6_OUTPUT_FILE, IPV6_START_ID, IPV6_BASE_GROUP_NAME)


def process_ipv4():
    """处理IPv4地址段"""
    print("\n" + "-" * 50)
    print("开始处理IPv4地址段...")
    all_ipv4 = []
    for source in IPV4_SOURCES:
        response = fetch_ip_data(source)
        if not response:
            continue
            
        parsed = get_cidrs_from_response(response)
        all_ipv4.extend(parsed)
        print(f"[+] 从 {source} 解析到 {len(parsed)} 条IPv4")

    if not all_ipv4:
        print("\n[❌] 未获取到有效IPv4地址段")
        return
        
    clean_ipv4 = clean_ip_data(all_ipv4)
    ipv4_chunks = split_into_chunks(clean_ipv4)
    print(f"[+] IPv4分块完成：{len(ipv4_chunks)}个块")
    records = generate_ikuai_records(ipv4_chunks, IPV4_START_ID, IPV4_BASE_GROUP_NAME)
    save_to_local(records, IPV4_OUTPUT_FILE, IPV4_START_ID, IPV4_BASE_GROUP_NAME)


if __name__ == "__main__":
    print("=" * 60)
    print("   爱快IP地址组生成脚本（IPv4+IPv6）")
    print(f"   生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    process_ipv4()  # 先处理IPv4（ID从60开始）
    process_ipv6()  # 再处理IPv6（ID从70开始）

    print("\n" + "=" * 60)
