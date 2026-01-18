#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供水管网巡检数据统计脚本
用于统计巡检数据，生成汇总报告
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys


class InspectionStats:
    """巡检数据统计类"""

    def __init__(self, data_file: str = None):
        """初始化统计数据"""
        self.inspections = []
        if data_file:
            self.load_data(data_file)

    def load_data(self, data_file: str):
        """从JSON文件加载巡检数据"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.inspections = data.get('inspections', [])
        except FileNotFoundError:
            print(f"错误：文件 {data_file} 不存在")
        except json.JSONDecodeError:
            print(f"错误：文件 {data_file} 格式不正确")

    def add_inspection(self, inspection: Dict[str, Any]):
        """添加单条巡检记录"""
        self.inspections.append(inspection)

    def filter_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """按日期范围筛选"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return [
            insp for insp in self.inspections
            if start <= datetime.strptime(insp['date'], '%Y-%m-%d') <= end
        ]

    def filter_by_area(self, area: str) -> List[Dict]:
        """按区域筛选"""
        return [
            insp for insp in self.inspections
            if insp.get('area') == area
        ]

    def filter_by_inspector(self, inspector: str) -> List[Dict]:
        """按巡检人员筛选"""
        return [
            insp for insp in self.inspections
            if insp.get('inspector') == inspector
        ]

    def calculate_statistics(self, inspections: List[Dict] = None) -> Dict[str, Any]:
        """计算统计数据"""
        if inspections is None:
            inspections = self.inspections

        total = len(inspections)
        if total == 0:
            return {
                'total': 0,
                'normal': 0,
                'problem': 0,
                'by_level': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
                'by_type': {},
                'by_area': {},
                'completion_rate': 0
            }

        normal = sum(1 for insp in inspections if insp.get('status') == '正常')
        problem = total - normal

        # 按问题等级统计
        by_level = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for insp in inspections:
            for prob in insp.get('problems', []):
                level = prob.get('level', 'D')
                by_level[level] += 1

        # 按设施类型统计
        by_type = {}
        for insp in inspections:
            for prob in insp.get('problems', []):
                type_name = prob.get('type', '其他')
                by_type[type_name] = by_type.get(type_name, 0) + 1

        # 按区域统计
        by_area = {}
        for insp in inspections:
            area = insp.get('area', '未知')
            by_area[area] = by_area.get(area, 0) + 1

        return {
            'total': total,
            'normal': normal,
            'problem': problem,
            'problem_rate': round(problem / total * 100, 2),
            'by_level': by_level,
            'by_type': by_type,
            'by_area': by_area,
            'completion_rate': round(sum(1 for insp in inspections if insp.get('completed')) / total * 100, 2)
        }

    def generate_report(self, statistics: Dict[str, Any]) -> str:
        """生成统计报告"""
        report = []
        report.append("=" * 60)
        report.append("供水管网巡检统计报告")
        report.append("=" * 60)
        report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 总体统计
        report.append("【总体统计】")
        report.append(f"  巡检点数：{statistics['total']} 点")
        report.append(f"  正常点数：{statistics['normal']} 点")
        report.append(f"  问题点数：{statistics['problem']} 点")
        report.append(f"  问题率：{statistics.get('problem_rate', 0)}%")
        report.append(f"  完成率：{statistics.get('completion_rate', 0)}%")
        report.append("")

        # 问题等级统计
        report.append("【问题等级统计】")
        report.append("  A-紧急：{} 个".format(statistics['by_level']['A']))
        report.append("  B-重要：{} 个".format(statistics['by_level']['B']))
        report.append("  C-一般：{} 个".format(statistics['by_level']['C']))
        report.append("  D-观察：{} 个".format(statistics['by_level']['D']))
        report.append("")

        # 按设施类型统计
        if statistics['by_type']:
            report.append("【按设施类型统计】")
            for type_name, count in sorted(statistics['by_type'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {type_name}：{count} 个")
            report.append("")

        # 按区域统计
        if statistics['by_area']:
            report.append("【按区域统计】")
            for area, count in sorted(statistics['by_area'].items()):
                report.append(f"  {area}：{count} 点")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def export_to_json(self, statistics: Dict[str, Any], output_file: str):
        """导出统计数据到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        print(f"统计数据已导出到：{output_file}")


def main():
    """主函数"""
    # 示例使用
    stats = InspectionStats()

    # 示例数据
    sample_data = [
        {
            "date": "2024-01-15",
            "area": "东区",
            "inspector": "张三",
            "status": "有问题",
            "completed": True,
            "problems": [
                {"type": "阀门", "id": "V-001", "level": "A", "description": "阀门无法关闭"},
                {"type": "井盖", "id": "M-005", "level": "C", "description": "标识不清"}
            ]
        },
        {
            "date": "2024-01-15",
            "area": "西区",
            "inspector": "李四",
            "status": "正常",
            "completed": True,
            "problems": []
        },
        {
            "date": "2024-01-16",
            "area": "东区",
            "inspector": "张三",
            "status": "有问题",
            "completed": True,
            "problems": [
                {"type": "水表", "id": "M-012", "level": "B", "description": "水表停走"}
            ]
        }
    ]

    for data in sample_data:
        stats.add_inspection(data)

    # 计算统计
    statistics = stats.calculate_statistics()

    # 生成报告
    report = stats.generate_report(statistics)
    print(report)

    # 导出JSON
    stats.export_to_json(statistics, "inspection_statistics.json")


if __name__ == "__main__":
    main()
