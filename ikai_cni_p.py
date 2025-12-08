import requests
import re
import os
from urllib.parse import urljoin

# 各省简称与名称映射
PROVINCE_MAPPING = {
    "AH": "安徽", "BJ": "北京", "CQ": "重庆", "FJ": "福建", "GD": "广东",
    "GS": "甘肃", "GX": "广西", "GZ": "贵州", "HA": "河南", "HB": "湖北",
    "HE": "河北", "HI": "海南", "HL": "黑龙江", "HN": "湖南", "JL": "吉林",
    "JS": "江苏", "JX": "江西", "LN": "辽宁", "NM": "内蒙古", "NX": "宁夏",
    "QH": "青海", "SC": "四川", "SD": "山东", "SH": "上海", "SN": "陕西",
    "SX": "山西", "TJ": "天津", "XJ": "新疆", "XZ": "西藏", "YN": "云南", "ZJ": "浙江"
}

BASE_REPO_URL = "https://raw.githubusercontent.com/metowolf/iplist/master/data/country/CN/"
IP_GROUP_FILENAME = "ikuai_cn_province_ipgroup.txt"
START_ID = 60
MAX_PER_GROUP = 1000  # 爱快单个分组上限


def validate_cidr(cidr):
    """验证IPv4 CIDR格式"""
    pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r'/([0-9]|[12][0-9]|3[0-2])$'
    )
    return pattern.match(cidr.strip()) is not None


def fetch_province_cidrs(province_code):
    """获取单个省份的IP段"""
    url = urljoin(BASE_REPO_URL, f"CN-{province_code}.txt")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        cidrs = []
        for line in r.text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and validate_cidr(line):
                cidrs.append(line)
        return cidrs
    except Exception as e:
        print(f"警告：获取{PROVINCE_MAPPING[province_code]}失败 - {e}")
        return []


def split_and_write(province_name, cidrs, current_id, f):
    """把一个省份的IP段按1000条拆分写入文件"""
    total = len(cidrs)
    if total == 0:
        return current_id

    part = 1
    for i in range(0, total, MAX_PER_GROUP):
        chunk = cidrs[i:i + MAX_PER_GROUP]
        group_name = f"{province_name}IP" if total <= MAX_PER_GROUP else f"{province_name}IP-{part}"
        addr_pool = ','.join(chunk)
        line = f"id={current_id} comment= type=0 group_name={group_name} addr_pool={addr_pool}\n"
        f.write(line)
        print(f"  → {group_name}：{len(chunk)}条（ID: {current_id}）")
        current_id += 1
        part += 1
    return current_id


def generate_ipgroup():
    if os.path.exists(IP_GROUP_FILENAME):
        os.remove(IP_GROUP_FILENAME)
        print(f"已删除旧文件：{IP_GROUP_FILENAME}\n")

    current_id = START_ID
    success_count = 0

    with open(IP_GROUP_FILENAME, 'w', encoding='utf-8') as f:
        for code in sorted(PROVINCE_MAPPING.keys()):
            name = PROVINCE_MAPPING[code]
            print(f"正在处理：{name}")
            cidrs = fetch_province_cidrs(code)
            if not cidrs:
                print(f"  跳过：无有效IP段\n")
                continue
            current_id = split_and_write(name, cidrs, current_id, f)
            success_count += 1
            print()  # 空行分隔

    last_id = current_id - 1
    print(f"生成完成！")
    print(f"文件：{IP_GROUP_FILENAME}")
    print(f"成功生成 {success_count} 个省份（部分省份自动拆分成多个分组）")
    print(f"分组ID范围：{START_ID} - {last_id}\n")


def main():
    print("=== 开始生成爱快国内IP分组（自动拆分≤1000条）===".center(50))
    print(f"数据来源：{BASE_REPO_URL}")
    print(f"目标文件：{IP_GROUP_FILENAME}\n")
    generate_ipgroup()
    print("=== 全部完成！直接复制文件内容到爱快批量导入即可 ===\n")


if __name__ == "__main__":
    main()
