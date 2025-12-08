import requests
import re
import os
from urllib.parse import urljoin

# 各省简称与名称映射（对应仓库文件前缀）
PROVINCE_MAPPING = {
    "AH": "安徽",
    "BJ": "北京",
    "CQ": "重庆",
    "FJ": "福建",
    "GD": "广东",
    "GS": "甘肃",
    "GX": "广西",
    "GZ": "贵州",
    "HA": "河南",
    "HB": "湖北",
    "HE": "河北",
    "HI": "海南",
    "HL": "黑龙江",
    "HN": "湖南",
    "JL": "吉林",
    "JS": "江苏",
    "JX": "江西",
    "LN": "辽宁",
    "NM": "内蒙古",
    "NX": "宁夏",
    "QH": "青海",
    "SC": "四川",
    "SD": "山东",
    "SH": "上海",
    "SN": "陕西",
    "SX": "山西",
    "TJ": "天津",
    "XJ": "新疆",
    "XZ": "西藏",
    "YN": "云南",
    "ZJ": "浙江"
}

# 仓库基础URL（各省IP文件地址）
BASE_REPO_URL = "https://raw.githubusercontent.com/metowolf/iplist/master/data/country/CN/"
IP_GROUP_FILENAME = "ikuai_cn_province_ipgroup.txt"  # 输出文件名
START_ID = 60  # ikuai分组起始ID
MAX_IP_PER_GROUP = 1000  # 爱快单个分组最大IP段数量


def validate_cidr(cidr):
    """验证IPv4 CIDR格式是否有效"""
    cidr_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r'/([0-9]|[12][0-9]|3[0-2])$'
    )
    return cidr_pattern.match(cidr.strip()) is not None


def fetch_province_cidrs(province_code):
    """获取单个省份的IP CIDR列表"""
    file_url = urljoin(BASE_REPO_URL, f"CN-{province_code}.txt")
    try:
        response = requests.get(file_url, timeout=15)
        response.raise_for_status()  # 抛出HTTP错误
        
        cidrs = []
        for line in response.text.splitlines():
            line = line.strip()
            # 过滤注释、空行，保留有效CIDR
            if line and not line.startswith('#') and validate_cidr(line):
                cidrs.append(line)
        
        return cidrs if cidrs else None
    
    except requests.exceptions.RequestException as e:
        print(f"警告：获取{PROVINCE_MAPPING[province_code]}IP失败 - {str(e)}")
        return None


def split_into_chunks(lst, chunk_size):
    """将列表拆分为指定大小的子列表"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def generate_province_ipgroup():
    """生成按省份分类的ikuai IP分组文件（支持超过1000条时自动拆分）"""
    # 清除旧文件
    if os.path.exists(IP_GROUP_FILENAME):
        os.remove(IP_GROUP_FILENAME)
        print(f"已删除旧文件：{IP_GROUP_FILENAME}")
    
    current_id = START_ID
    success_count = 0
    total_groups = 0
    
    with open(IP_GROUP_FILENAME, 'w', encoding='utf-8') as f:
        # 遍历所有省份，按简称排序
        for province_code in sorted(PROVINCE_MAPPING.keys()):
            province_name = PROVINCE_MAPPING[province_code]
            print(f"正在处理：{province_name}...")
            
            # 获取该省份的CIDR列表
            cidrs = fetch_province_cidrs(province_code)
            if not cidrs:
                print(f"跳过：{province_name}无有效IP段\n")
                continue
            
            # 计算需要拆分的组数
            total_cidrs = len(cidrs)
            num_chunks = (total_cidrs + MAX_IP_PER_GROUP - 1) // MAX_IP_PER_GROUP  # 向上取整
            
            # 拆分并写入多个分组
            for i, chunk in enumerate(split_into_chunks(cidrs, MAX_IP_PER_GROUP), 1):
                # 组名格式：省份名称IP(1)、省份名称IP(2)等
                group_name = f"{province_name}IP" + (f"({i})" if num_chunks > 1 else "")
                addr_pool = ','.join(chunk)
                
                # 写入爱快格式
                line = f"id={current_id} comment= type=0 group_name={group_name} addr_pool={addr_pool}\n"
                f.write(line)
                
                print(f"成功：{group_name} - {len(chunk)}个IP段 - ID:{current_id}")
                current_id += 1
                total_groups += 1
            
            success_count += 1
            print(f"{province_name}处理完成，共{num_chunks}个分组，{total_cidrs}个IP段\n")
    
    print(f"\n生成完成！文件：{IP_GROUP_FILENAME}")
    print(f"统计：成功处理{success_count}个省份（共{len(PROVINCE_MAPPING)}个省份）")
    print(f"生成总分组数：{total_groups}")
    print(f"分组ID范围：{START_ID} - {current_id - 1}")


def main():
    print("=== 开始生成ikuai省份IP分组文件 ===")
    print(f"数据来源：{BASE_REPO_URL}")
    print(f"目标文件：{IP_GROUP_FILENAME}")
    print(f"单个分组最大IP段限制：{MAX_IP_PER_GROUP}\n")
    
    generate_province_ipgroup()
    print("\n=== 生成结束 ===")


if __name__ == "__main__":
    main()
