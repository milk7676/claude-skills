#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供水管网设备台账统计脚本
统计设备资产、健康状况、维护记录
"""

import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict


class AssetStatistics:
    """设备资产统计类"""

    def __init__(self):
        """初始化统计对象"""
        self.assets = []

    def add_asset(self, asset: Dict[str, Any]):
        """添加设备资产"""
        self.assets.append(asset)

    def load_from_json(self, data_file: str):
        """从JSON文件加载资产数据"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assets = data.get('assets', [])
        except FileNotFoundError:
            print(f"错误：文件 {data_file} 不存在")
        except json.JSONDecodeError:
            print(f"错误：文件 {data_file} 格式不正确")

    def get_total_count(self) -> int:
        """获取资产总数"""
        return len(self.assets)

    def get_total_value(self) -> float:
        """获取资产总价值"""
        return sum(asset.get('original_value', 0) for asset in self.assets)

    def get_net_value(self) -> float:
        """获取资产净值"""
        return sum(asset.get('net_value', 0) for asset in self.assets)

    def get_depreciation_rate(self) -> float:
        """获取平均折旧率"""
        total = self.get_total_value()
        net = self.get_net_value()
        return ((total - net) / total * 100) if total > 0 else 0

    def group_by_type(self) -> Dict[str, Dict[str, Any]]:
        """按设备类型分组统计"""
        groups = defaultdict(lambda: {
            'count': 0,
            'original_value': 0,
            'net_value': 0,
            'avg_age': 0
        })

        for asset in self.assets:
            asset_type = asset.get('type', '未知')
            groups[asset_type]['count'] += 1
            groups[asset_type]['original_value'] += asset.get('original_value', 0)
            groups[asset_type]['net_value'] += asset.get('net_value', 0)

        # 计算平均年限
        for asset in self.assets:
            asset_type = asset.get('type', '未知')
            groups[asset_type]['avg_age'] += asset.get('age', 0)

        for key in groups:
            if groups[key]['count'] > 0:
                groups[key]['avg_age'] = round(groups[key]['avg_age'] / groups[key]['count'], 1)
                groups[key]['original_value'] = round(groups[key]['original_value'], 2)
                groups[key]['net_value'] = round(groups[key]['net_value'], 2)

        return dict(groups)

    def group_by_health(self) -> Dict[str, Dict[str, Any]]:
        """按健康状况分组统计"""
        groups = defaultdict(lambda: {'count': 0, 'total_value': 0})
        for asset in self.assets:
            health = asset.get('health', 'D')
            groups[health]['count'] += 1
            groups[health]['total_value'] += asset.get('net_value', 0)

        # 计算百分比
        total = len(self.assets)
        for key in groups:
            groups[key]['percentage'] = round(groups[key]['count'] / total * 100, 1) if total > 0 else 0

        return dict(groups)

    def group_by_age_range(self) -> Dict[str, int]:
        """按使用年限分组统计"""
        ranges = {'0-5年': 0, '5-10年': 0, '10-20年': 0, '20-30年': 0, '30年以上': 0}
        for asset in self.assets:
            age = asset.get('age', 0)
            if age < 5:
                ranges['0-5年'] += 1
            elif age < 10:
                ranges['5-10年'] += 1
            elif age < 20:
                ranges['10-20年'] += 1
            elif age < 30:
                ranges['20-30年'] += 1
            else:
                ranges['30年以上'] += 1
        return ranges

    def get_maintenance_overdue(self, overdue_days: int = 30) -> List[Dict[str, Any]]:
        """获取超期未维护的设备"""
        today = datetime.now()
        overdue_assets = []

        for asset in self.assets:
            next_maintenance_str = asset.get('next_maintenance')
            if next_maintenance_str:
                try:
                    next_maintenance = datetime.strptime(next_maintenance_str, '%Y-%m-%d')
                    days_overdue = (today - next_maintenance).days
                    if days_overdue > overdue_days:
                        overdue_assets.append({
                            **asset,
                            'days_overdue': days_overdue
                        })
                except ValueError:
                    pass

        return overdue_assets

    def get_replacement_candidates(self, min_age: int = 25, health: str = 'D') -> List[Dict[str, Any]]:
        """获取需要更换的候选设备"""
        candidates = []
        for asset in self.assets:
            if asset.get('age', 0) >= min_age or asset.get('health') == health:
                candidates.append(asset)
        return candidates

    def calculate_depreciation(self, asset: Dict[str, Any]) -> float:
        """
        计算设备折旧（直线法）

        Args:
            asset: 资产信息
        Returns:
            净值
        """
        original = asset.get('original_value', 0)
        useful_life = asset.get('useful_life', 30)
        age = asset.get('age', 0)

        if useful_life > 0:
            annual_depreciation = original / useful_life
            accumulated = annual_depreciation * age
            net_value = max(0, original - accumulated)
        else:
            net_value = original

        return round(net_value, 2)

    def generate_report(self) -> str:
        """生成统计报告"""
        report = []
        report.append("=" * 70)
        report.append("供水管网设备资产统计报告")
        report.append("=" * 70)
        report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 总体统计
        report.append("【总体统计】")
        report.append(f"  资产总数：{self.get_total_count()} 台/个")
        report.append(f"  资产原值：{self.get_total_value():,.2f} 元")
        report.append(f"  资产净值：{self.get_net_value():,.2f} 元")
        report.append(f"  累计折旧：{self.get_total_value() - self.get_net_value():,.2f} 元")
        report.append(f"  折旧率：{self.get_depreciation_rate():.2f}%")
        report.append("")

        # 按设备类型
        by_type = self.group_by_type()
        if by_type:
            report.append("【按设备类型统计】")
            report.append(f"{'类型':<15} {'数量':>8} {'原值(万)':>12} {'净值(万)':>12} {'平均年限':>10}")
            report.append("-" * 70)
            for type_name, data in sorted(by_type.items()):
                report.append(f"{type_name:<15} {data['count']:>8} {data['original_value']/10000:>12.2f} {data['net_value']/10000:>12.2f} {data['avg_age']:>10}")
            report.append("")

        # 按健康状况
        by_health = self.group_by_health()
        if by_health:
            report.append("【按健康状况统计】")
            health_desc = {'A': 'A-优秀', 'B': 'B-良好', 'C': 'C-一般', 'D': 'D-需关注'}
            for health in ['A', 'B', 'C', 'D']:
                if health in by_health:
                    data = by_health[health]
                    report.append(f"  {health_desc[health]}：{data['count']} 台 ({data['percentage']}%) - 净值 {data['total_value']:,.2f} 元")
            report.append("")

        # 按使用年限
        by_age = self.group_by_age_range()
        if by_age:
            report.append("【按使用年限统计】")
            for age_range, count in by_age.items():
                percentage = count / self.get_total_count() * 100 if self.get_total_count() > 0 else 0
                report.append(f"  {age_range}：{count} 台 ({percentage:.1f}%)")
            report.append("")

        # 超期未维护
        overdue = self.get_maintenance_overdue()
        if overdue:
            report.append("【超期未维护设备】")
            for asset in overdue[:5]:  # 只显示前5个
                report.append(f"  {asset.get('name')} - 超期 {asset.get('days_overdue')} 天")
            if len(overdue) > 5:
                report.append(f"  ... 共 {len(overdue)} 台")
            report.append("")

        # 更换候选
        candidates = self.get_replacement_candidates()
        if candidates:
            report.append("【建议更换设备】")
            for asset in candidates[:5]:  # 只显示前5个
                report.append(f"  {asset.get('name')} - 使用年限 {asset.get('age')} 年 - 健康等级 {asset.get('health')}")
            if len(candidates) > 5:
                report.append(f"  ... 共 {len(candidates)} 台")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def export_to_json(self, output_file: str = "asset_statistics.json"):
        """导出统计数据到JSON"""
        stats = {
            'timestamp': str(datetime.now()),
            'summary': {
                'total_count': self.get_total_count(),
                'total_value': self.get_total_value(),
                'net_value': self.get_net_value(),
                'depreciation_rate': self.get_depreciation_rate()
            },
            'by_type': self.group_by_type(),
            'by_health': self.group_by_health(),
            'by_age_range': self.group_by_age_range(),
            'overdue_maintenance': len(self.get_maintenance_overdue()),
            'replacement_candidates': len(self.get_replacement_candidates())
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"统计数据已导出到：{output_file}")


def main():
    """主函数 - 示例使用"""
    stats = AssetStatistics()

    # 示例设备数据
    sample_assets = [
        {
            'id': 'V-001',
            'name': 'DN500闸阀',
            'type': '阀门',
            'material': '球墨铸铁',
            'original_value': 45000,
            'useful_life': 30,
            'age': 8,
            'health': 'B',
            'next_maintenance': '2024-02-01'
        },
        {
            'id': 'P-001',
            'name': 'PE管DN200',
            'type': '管道',
            'material': 'PE',
            'original_value': 12000,
            'useful_life': 50,
            'age': 3,
            'health': 'A',
            'next_maintenance': '2024-06-15'
        },
        {
            'id': 'V-002',
            'name': 'DN300蝶阀',
            'type': '阀门',
            'material': '球墨铸铁',
            'original_value': 28000,
            'useful_life': 30,
            'age': 28,
            'health': 'D',
            'next_maintenance': '2023-12-01'  # 已超期
        },
        {
            'id': 'M-001',
            'name': '离心泵200QJ',
            'type': '水泵',
            'material': '不锈钢',
            'original_value': 150000,
            'useful_life': 15,
            'age': 12,
            'health': 'C',
            'next_maintenance': '2024-01-20'
        }
    ]

    for asset in sample_assets:
        # 计算净值
        asset['net_value'] = stats.calculate_depreciation(asset)
        stats.add_asset(asset)

    # 生成报告
    print(stats.generate_report())

    # 导出JSON
    stats.export_to_json()


if __name__ == "__main__":
    main()
