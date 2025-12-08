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


def generate_province_ipgroup():
    """生成按省份分类的ikuai IP分组文件"""
    # 清除旧文件
    if os.path.exists(IP_GROUP_FILENAME):
        os.remove(IP_GROUP_FILENAME)
        print(f"已删除旧文件：{IP_GROUP_FILENAME}")
    
    current_id = START_ID
    success_count = 0
    
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
            
            # 按ikuai格式写入（支持超过1000个IP段，自动适配）
            addr_pool = ','.join(cidrs)
            # ikuai分组格式：id=xx comment= type=0 group_name=省份名称 addr_pool=CIDR1,CIDR2,...
            line = f"id={current_id} comment= type=0 group_name={province_name}IP addr_pool={addr_pool}\n"
            f.write(line)
            
            print(f"成功：{province_name} - {len(cidrs)}个IP段 - ID:{current_id}")
            current_id += 1
            success_count += 1
            print()  # 空行分隔
    
    print(f"\n生成完成！文件：{IP_GROUP_FILENAME}")
    print(f"统计：成功生成{success_count}个省份分组（共{len(PROVINCE_MAPPING)}个省份）")
    print(f"分组ID范围：{START_ID} - {current_id - 1}")


def main():
    print("=== 开始生成ikuai省份IP分组文件 ===")
    print(f"数据来源：{BASE_REPO_URL}")
    print(f"目标文件：{IP_GROUP_FILENAME}\n")
    
    generate_province_ipgroup()
    print("\n=== 生成结束 ===")


if __name__ == "__main__":
    main()
