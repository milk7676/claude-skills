#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供水管网维修工单统计脚本
统计工单数据、分析维修趋势、评估人员绩效
"""

import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class WorkOrderStatistics:
    """工单统计类"""

    def __init__(self):
        """初始化统计对象"""
        self.work_orders = []

    def add_work_order(self, work_order: Dict[str, Any]):
        """添加工单"""
        self.work_orders.append(work_order)

    def load_from_json(self, data_file: str):
        """从JSON文件加载工单数据"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.work_orders = data.get('work_orders', [])
        except FileNotFoundError:
            print(f"错误：文件 {data_file} 不存在")
        except json.JSONDecodeError:
            print(f"错误：文件 {data_file} 格式不正确")

    def filter_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """按日期范围筛选"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return [
            wo for wo in self.work_orders
            if start <= datetime.strptime(wo['created_date'], '%Y-%m-%d') <= end
        ]

    def filter_by_type(self, order_type: str) -> List[Dict]:
        """按工单类型筛选"""
        return [
            wo for wo in self.work_orders
            if wo.get('type') == order_type
        ]

    def filter_by_status(self, status: str) -> List[Dict]:
        """按工单状态筛选"""
        return [
            wo for wo in self.work_orders
            if wo.get('status') == status
        ]

    def filter_by_area(self, area: str) -> List[Dict]:
        """按区域筛选"""
        return [
            wo for wo in self.work_orders
            if wo.get('area') == area
        ]

    def group_by_type(self) -> Dict[str, Dict[str, Any]]:
        """按工单类型分组统计"""
        groups = defaultdict(lambda: {
            'count': 0,
            'completed': 0,
            'total_duration': 0,
            'total_cost': 0
        })

        for wo in self.work_orders:
            order_type = wo.get('type', '其他')
            groups[order_type]['count'] += 1
            if wo.get('status') == '已完成':
                groups[order_type]['completed'] += 1
            groups[order_type]['total_duration'] += wo.get('duration_hours', 0)
            groups[order_type]['total_cost'] += wo.get('cost', 0)

        # 计算统计值
        for key in groups:
            data = groups[key]
            data['completion_rate'] = round(data['completed'] / data['count'] * 100, 1) if data['count'] > 0 else 0
            data['avg_duration'] = round(data['total_duration'] / data['completed'], 2) if data['completed'] > 0 else 0
            data['total_cost'] = round(data['total_cost'], 2)

        return dict(groups)

    def group_by_area(self) -> Dict[str, int]:
        """按区域分组统计"""
        groups = defaultdict(int)
        for wo in self.work_orders:
            area = wo.get('area', '未知')
            groups[area] += 1
        return dict(groups)

    def group_by_fault_type(self) -> Dict[str, int]:
        """按故障类型分组统计"""
        groups = defaultdict(int)
        for wo in self.work_orders:
            fault_type = wo.get('fault_type', '其他')
            groups[fault_type] += 1
        return dict(groups)

    def calculate_personnel_performance(self) -> Dict[str, Dict[str, Any]]:
        """计算人员绩效"""
        personnel = defaultdict(lambda: {
            'orders': [],
            'count': 0,
            'completed': 0,
            'total_duration': 0
        })

        for wo in self.work_orders:
            staff = wo.get('staff', '未知')
            personnel[staff]['orders'].append(wo)
            personnel[staff]['count'] += 1
            if wo.get('status') == '已完成':
                personnel[staff]['completed'] += 1
                personnel[staff]['total_duration'] += wo.get('duration_hours', 0)

        # 计算绩效指标
        result = {}
        for staff, data in personnel.items():
            completed_orders = [wo for wo in data['orders'] if wo.get('status') == '已完成']
            durations = [wo.get('duration_hours', 0) for wo in completed_orders]

            result[staff] = {
                'total_orders': data['count'],
                'completed': data['completed'],
                'completion_rate': round(data['completed'] / data['count'] * 100, 1) if data['count'] > 0 else 0,
                'total_duration': round(data['total_duration'], 2),
                'avg_duration': round(statistics.mean(durations), 2) if durations else 0,
                'min_duration': round(min(durations), 2) if durations else 0,
                'max_duration': round(max(durations), 2) if durations else 0
            }

        return result

    def calculate_trend(self, days: int = 30) -> Dict[str, Any]:
        """计算工单趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 按天分组
        daily_stats = defaultdict(int)
        for wo in self.work_orders:
            wo_date = datetime.strptime(wo['created_date'], '%Y-%m-%d')
            if start_date <= wo_date <= end_date:
                date_str = wo_date.strftime('%Y-%m-%d')
                daily_stats[date_str] += 1

        return {
            'period_days': days,
            'total_orders': sum(daily_stats.values()),
            'avg_per_day': round(sum(daily_stats.values()) / days, 1),
            'daily_stats': dict(daily_stats)
        }

    def get_overdue_orders(self, overdue_hours: int = 48) -> List[Dict[str, Any]]:
        """获取超期未完成的工单"""
        now = datetime.now()
        overdue_orders = []

        for wo in self.work_orders:
            if wo.get('status') not in ['已完成', '已取消']:
                created_date = datetime.strptime(wo['created_date'], '%Y-%m-%d')
                if wo.get('created_time'):
                    created_date = datetime.strptime(f"{wo['created_date']} {wo['created_time']}", '%Y-%m-%d %H:%M')

                hours_elapsed = (now - created_date).total_seconds() / 3600
                if hours_elapsed > overdue_hours:
                    overdue_orders.append({
                        **wo,
                        'hours_elapsed': round(hours_elapsed, 1)
                    })

        return overdue_orders

    def generate_report(self) -> str:
        """生成统计报告"""
        report = []
        report.append("=" * 70)
        report.append("供水管网维修工单统计报告")
        report.append("=" * 70)
        report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 总体统计
        total_orders = len(self.work_orders)
        completed = sum(1 for wo in self.work_orders if wo.get('status') == '已完成')

        report.append("【总体统计】")
        report.append(f"  工单总数：{total_orders} 单")
        report.append(f"  已完成：{completed} 单")
        report.append(f"  进行中：{total_orders - completed} 单")
        report.append(f"  完成率：{round(completed / total_orders * 100, 1) if total_orders > 0 else 0}%")
        report.append("")

        # 按工单类型
        by_type = self.group_by_type()
        if by_type:
            report.append("【按工单类型统计】")
            report.append(f"{'类型':<12} {'数量':>6} {'完成':>6} {'完成率':>8} {'平均用时(h)':>12}")
            report.append("-" * 70)
            type_order = {'抢修': 1, '维修': 2, '改造': 3, '安装': 4, '巡检': 5, '其他': 99}
            for type_name in sorted(by_type.keys(), key=lambda x: type_order.get(x, 99)):
                data = by_type[type_name]
                report.append(f"{type_name:<12} {data['count']:>6} {data['completed']:>6} {data['completion_rate']:>7}% {data['avg_duration']:>12}")
            report.append("")

        # 按区域统计
        by_area = self.group_by_area()
        if by_area:
            report.append("【按区域统计】")
            for area, count in sorted(by_area.items()):
                percentage = count / total_orders * 100 if total_orders > 0 else 0
                report.append(f"  {area}：{count} 单 ({percentage:.1f}%)")
            report.append("")

        # 按故障类型
        by_fault = self.group_by_fault_type()
        if by_fault:
            report.append("【按故障类型统计】")
            for fault_type, count in sorted(by_fault.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total_orders * 100 if total_orders > 0 else 0
                report.append(f"  {fault_type}：{count} 单 ({percentage:.1f}%)")
            report.append("")

        # 人员绩效
        personnel = self.calculate_personnel_performance()
        if personnel:
            report.append("【人员绩效统计】")
            report.append(f"{'人员':<10} {'总工单':>8} {'完成':>6} {'完成率':>8} {'平均用时(h)':>12}")
            report.append("-" * 70)
            for staff, data in sorted(personnel.items(), key=lambda x: x[1]['completed'], reverse=True):
                report.append(f"{staff:<10} {data['total_orders']:>8} {data['completed']:>6} {data['completion_rate']:>7}% {data['avg_duration']:>12}")
            report.append("")

        # 超期工单
        overdue = self.get_overdue_orders()
        if overdue:
            report.append("【超期未完成工单】")
            for wo in overdue[:5]:
                report.append(f"  {wo.get('order_id')} - 已超期 {wo.get('hours_elapsed')} 小时")
            if len(overdue) > 5:
                report.append(f"  ... 共 {len(overdue)} 单")
            report.append("")

        # 近期趋势
        trend = self.calculate_trend(days=30)
        report.append("【近30天趋势】")
        report.append(f"  工单总数：{trend['total_orders']} 单")
        report.append(f"  日均工单：{trend['avg_per_day']} 单/天")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def export_to_json(self, output_file: str = "workorder_statistics.json"):
        """导出统计数据到JSON"""
        stats = {
            'timestamp': str(datetime.now()),
            'summary': {
                'total_orders': len(self.work_orders),
                'completed': sum(1 for wo in self.work_orders if wo.get('status') == '已完成'),
                'completion_rate': round(sum(1 for wo in self.work_orders if wo.get('status') == '已完成') / len(self.work_orders) * 100, 1) if self.work_orders else 0
            },
            'by_type': self.group_by_type(),
            'by_area': self.group_by_area(),
            'by_fault_type': self.group_by_fault_type(),
            'personnel_performance': self.calculate_personnel_performance(),
            'trend': self.calculate_trend(days=30),
            'overdue_orders': len(self.get_overdue_orders())
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"统计数据已导出到：{output_file}")


def main():
    """主函数 - 示例使用"""
    stats = WorkOrderStatistics()

    # 示例工单数据
    sample_orders = [
        {
            'order_id': 'WO-20240115-EMG-001',
            'type': '抢修',
            'status': '已完成',
            'created_date': '2024-01-15',
            'created_time': '09:30',
            'completed_date': '2024-01-15',
            'area': '东区',
            'staff': '刘师傅',
            'fault_type': '管道爆裂',
            'duration_hours': 5.5,
            'cost': 2500
        },
        {
            'order_id': 'WO-20240115-REP-002',
            'type': '维修',
            'status': '已完成',
            'created_date': '2024-01-15',
            'created_time': '10:00',
            'completed_date': '2024-01-16',
            'area': '西区',
            'staff': '张师傅',
            'fault_type': '阀门故障',
            'duration_hours': 8.0,
            'cost': 800
        },
        {
            'order_id': 'WO-20240116-REP-003',
            'type': '维修',
            'status': '进行中',
            'created_date': '2024-01-16',
            'created_time': '08:30',
            'area': '东区',
            'staff': '刘师傅',
            'fault_type': '水表故障',
            'duration_hours': 0,
            'cost': 0
        },
        {
            'order_id': 'WO-20240117-INS-004',
            'type': '巡检',
            'status': '已完成',
            'created_date': '2024-01-17',
            'created_time': '09:00',
            'completed_date': '2024-01-17',
            'area': '南区',
            'staff': '小李',
            'fault_type': '无',
            'duration_hours': 4.0,
            'cost': 0
        }
    ]

    for order in sample_orders:
        stats.add_work_order(order)

    # 生成报告
    print(stats.generate_report())

    # 导出JSON
    stats.export_to_json()


if __name__ == "__main__":
    main()
