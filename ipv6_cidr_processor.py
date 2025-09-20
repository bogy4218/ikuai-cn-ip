import requests
import re
import os
from datetime import datetime

# -------------------------- 核心配置参数 --------------------------
IPV6_SOURCES = [
    "https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest",  # APNIC官方数据源
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/ipv6.txt"  # 替换为有效第三方数据源
]
OUTPUT_FILE = "ikuai_cn_ipv6group.txt"
START_ID = 70
BASE_GROUP_NAME = "国内IPv6"
RECORDS_PER_ID = 1000
# ------------------------------------------------------------------


def fetch_ipv6_data(url):
    """从指定URL获取IPv6地址段原始数据"""
    try:
        print(f"[+] 正在获取数据源：{url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        print(f"[-] 错误：获取 {url} 超时（连接超时15秒）")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[-] 错误：获取 {url} 失败（HTTP状态码：{e.response.status_code}）")
        return None
    except Exception as e:
        print(f"[-] 错误：获取 {url} 异常 - {str(e)}")
        return None


def parse_apnic_data(raw_data):
    """解析APNIC格式数据"""
    ipv6_cidr_list = []
    if not raw_data:
        return ipv6_cidr_list

    lines = raw_data.split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) >= 7 and parts[1] == "CN" and parts[2] == "ipv6":
            ipv6_cidr = f"{parts[3]}/{parts[4]}"
            ipv6_cidr_list.append(ipv6_cidr.lower())
    return ipv6_cidr_list


def parse_plain_cidr(raw_data):
    """解析纯IPv6 CIDR格式数据"""
    ipv6_cidr_list = []
    if not raw_data:
        return ipv6_cidr_list

    ipv6_pattern = re.compile(r"^[0-9a-fA-F:]+/\d{1,3}$")
    lines = raw_data.split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and ipv6_pattern.match(line):
            ipv6_cidr_list.append(line.lower())
    return ipv6_cidr_list


def clean_ipv6_data(ipv6_list):
    """清洗IPv6地址段：去重+排序"""
    unique_sorted_list = sorted(list(set(ipv6_list)))
    print(f"[+] 数据清洗完成：{len(ipv6_list)}条原始数据 → {len(unique_sorted_list)}条去重后数据")
    return unique_sorted_list


def split_into_chunks(lst, chunk_size=RECORDS_PER_ID):
    """将长列表拆分为固定大小的块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def generate_ikuai_records(ipv6_chunks):
    """生成爱快路由器格式记录"""
    records = []
    current_id = START_ID

    for index, chunk in enumerate(ipv6_chunks):
        group_name = f"{BASE_GROUP_NAME}-{index + 1}"
        comment = ",%20".join(chunk)
        addr_pool = ",".join([cidr.split("/")[0] for cidr in chunk])
        records.append(f"id={current_id} comment={comment} group_name={group_name} addr_pool={addr_pool}")
        current_id += 1

    return records


def save_to_local(records, filename):
    """将生成的记录保存到本地文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(records))
        
        total_addresses = sum(len(record.split(",%20")) for record in records)
        print(f"\n[✅] 文件生成成功！")
        print(f"[📁] 文件路径：{os.path.abspath(filename)}")
        print(f"[📊] 统计信息：")
        print(f"     - 记录条数：{len(records)}")
        print(f"     - ID范围：{START_ID} ~ {START_ID + len(records) - 1}")
        print(f"     - 组名称：{BASE_GROUP_NAME}-1 ~ {BASE_GROUP_NAME}-{len(records)}")
        print(f"     - 地址段总数：{total_addresses}")
    except PermissionError:
        print(f"[-] 保存失败：无权限写入文件 {filename}（请检查路径权限）")
    except Exception as e:
        print(f"[-] 保存失败：{str(e)}")


if __name__ == "__main__":
    # 仅保留首尾各一个分隔线，去除冗余=符号输出
    print("=" * 60)
    print("   爱快IPv6国内地址组生成脚本")
    print(f"   生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 获取并解析IPv6地址段
    all_ipv6 = []
    for source in IPV6_SOURCES:
        raw_data = fetch_ipv6_data(source)
        if not raw_data:
            continue
        if "apnic.net" in source:
            parsed_data = parse_apnic_data(raw_data)
        else:
            parsed_data = parse_plain_cidr(raw_data)
        all_ipv6.extend(parsed_data)
        print(f"[+] 从 {source} 解析到 {len(parsed_data)} 条IPv6地址段")

    # 2. 数据校验与清洗
    if not all_ipv6:
        print("\n[❌] 错误：未获取到任何有效IPv6地址段，请检查网络或数据源有效性")
        exit(1)
    clean_ipv6 = clean_ipv6_data(all_ipv6)

    # 3. 拆分地址段为块
    ipv6_chunks = split_into_chunks(clean_ipv6)
    print(f"[+] 地址段分块完成：共拆分为 {len(ipv6_chunks)} 个块（每个块{RECORDS_PER_ID}条）")

    # 4. 生成记录并保存
    ikuai_records = generate_ikuai_records(ipv6_chunks)
    save_to_local(ikuai_records, OUTPUT_FILE)

    # 仅保留结尾一个分隔线
    print("\n" + "=" * 60)
    