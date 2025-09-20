# ikuai-cn-ip

## 项目简介

本仓库提供自动生成适用于爱快（iKuai）路由器的国内IPv4和IPv6地址分组文件的工具，帮助用户快速配置路由策略，实现国内IP地址的精准管理。

## 功能说明
1. **自动获取国内IP段**：通过定期拉取公开的国内IPv4和IPv6 CIDR列表
   - IPv4数据源：`https://metowolf.github.io/iplist/data/special/china.txt`、`https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/text/cn.txt`
   - IPv6数据源：`https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest`、`https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chn_ip_v6.txt`
2. **格式化处理**：将IP段转换为爱快路由器支持的IP分组格式
3. **分组优化**：每1000个IP段自动分为一组，便于路由器高效处理
4. **定时更新**：通过GitHub Actions每天自动更新IP分组文件，确保列表时效性

## 生成文件说明
- 生成的IPv4分组文件名为 `ikuai_cn_ipv4group.txt`
- 生成的IPv6分组文件名为 `ikuai_cn_ipv6group.txt`
- 文件格式示例：`id=60 comment=1.0.1.0/24,1.0.2.0/23,... group_name=国内IPv4-1 addr_pool=1.0.1.0,1.0.2.0,...`
  - `id`：分组ID（IPv4从60开始递增，IPv6从70开始递增）
  - `group_name`：分组名称（按序号递增，如国内IPv4-1、国内IPv6-1）
  - `addr_pool`：包含的IP段列表（CIDR格式的网络部分）
  - `comment`：包含的完整CIDR列表（用于参考）

## 使用方法
1. 从仓库下载最新的 `ikuai_cn_ipv4group.txt` 和 `ikuai_cn_ipv6group.txt` 文件
2. 登录爱快路由器管理后台
3. 进入 **网络设置 > IP分组** 页面
4. 分别导入IPv4和IPv6分组文件或手动粘贴内容，完成国内IP分组配置

## 自动更新机制
通过GitHub Actions实现每日自动更新：
- 运行时间：每天北京时间02:00（UTC时间18:00）
- 执行流程：拉取最新代码 → 运行生成脚本 → 提交更新后的IP分组文件

## 依赖说明
- Python 3.10+
- 依赖库：`requests`（用于获取IP列表）

## 注意事项
- 生成的IP分组文件会覆盖旧文件，确保每次使用的都是最新版本
- 若需调整更新频率，可修改GitHub Actions工作流中的Cron表达式
- IPv4和IPv6分组使用不同的ID范围，避免冲突（IPv4从60开始，IPv6从70开始）
