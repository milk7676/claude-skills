#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供水管网漏损率计算脚本
计算DMA分区漏损率、MNF分析、压力异常检测
"""

import json
from typing import Dict, List, Any
import statistics


class LeakageCalculator:
    """漏损率计算类"""

    def __init__(self):
        """初始化计算器"""
        self.dma_data = {}

    def add_dma_data(self, dma_id: str, total_flow: float, user_flows: List[float]):
        """
        添加DMA数据

        Args:
            dma_id: DMA分区ID
            total_flow: 总表读数 (m³)
            user_flows: 各用户表读数列表 (m³)
        """
        user_total = sum(user_flows)
        leakage = total_flow - user_total
        leakage_rate = (leakage / total_flow * 100) if total_flow > 0 else 0

        self.dma_data[dma_id] = {
            'total_flow': total_flow,
            'user_total': user_total,
            'user_flows': user_flows,
            'leakage': leakage,
            'leakage_rate': leakage_rate
        }

    def calculate_mnf(self, flow_data: List[Dict[str, str]], hour_range: tuple = (2, 4)) -> Dict[str, Any]:
        """
        计算夜间最小流量 (MNF)

        Args:
            flow_data: 流量数据列表 [{"time": "02:15", "flow": 120.5}, ...]
            hour_range: 分析时段 (start_hour, end_hour)
        """
        # 筛选指定时段的数据
        filtered_data = []
        for data in flow_data:
            hour = int(data['time'].split(':')[0])
            if hour_range[0] <= hour < hour_range[1]:
                filtered_data.append(float(data['flow']))

        if not filtered_data:
            return {
                'mnf': 0,
                'avg_flow': 0,
                'data_points': 0
            }

        mnf = min(filtered_data)
        avg_flow = sum(filtered_data) / len(filtered_data)

        return {
            'mnf': round(mnf, 2),
            'avg_flow': round(avg_flow, 2),
            'data_points': len(filtered_data),
            'flow_values': [round(f, 2) for f in filtered_data]
        }

    def detect_pressure_anomaly(self, pressure_data: List[Dict[str, Any]],
                               threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        压力异常检测

        Args:
            pressure_data: 压力数据 [{"time": "10:00", "pressure": 0.45}, ...]
            threshold: 异常阈值（相对于平均值的偏差比例）
        """
        pressures = [float(d['pressure']) for d in pressure_data]
        avg_pressure = statistics.mean(pressures)
        std_pressure = statistics.stdev(pressures) if len(pressures) > 1 else 0

        anomalies = []

        for i, data in enumerate(pressure_data):
            pressure = float(data['pressure'])
            deviation = abs(pressure - avg_pressure) / avg_pressure if avg_pressure > 0 else 0

            if deviation > threshold:
                anomalies.append({
                    'index': i,
                    'time': data['time'],
                    'pressure': pressure,
                    'avg_pressure': round(avg_pressure, 3),
                    'deviation': round(deviation * 100, 2),
                    'type': 'low' if pressure < avg_pressure else 'high'
                })

        return {
            'avg_pressure': round(avg_pressure, 3),
            'std_pressure': round(std_pressure, 3),
            'min_pressure': round(min(pressures), 3),
            'max_pressure': round(max(pressures), 3),
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }

    def assess_leakage_status(self, leakage_rate: float) -> Dict[str, Any]:
        """
        评估漏损状态

        Args:
            leakage_rate: 漏损率 (%)
        """
        if leakage_rate < 10:
            status = 'excellent'
            level = 'A-优秀'
            action = '保持现状，正常维护'
        elif leakage_rate < 15:
            status = 'good'
            level = 'B-良好'
            action = '关注漏损变化，加强巡检'
        elif leakage_rate < 25:
            status = 'warning'
            level = 'C-需关注'
            action = '排查漏水点，制定整改计划'
        else:
            status = 'critical'
            level = 'D-严重'
            action = '立即启动DMA分区分区检测，重点排查'

        return {
            'status': status,
            'level': level,
            'action': action,
            'urgency': '高' if leakage_rate >= 25 else '中' if leakage_rate >= 15 else '低'
        }

    def generate_dma_report(self, dma_id: str = None) -> str:
        """生成DMA漏损报告"""
        report = []
        report.append("=" * 70)
        report.append("供水管网DMA分区漏损分析报告")
        report.append("=" * 70)

        dmas = [dma_id] if dma_id else self.dma_data.keys()

        for dma in dmas:
            if dma not in self.dma_data:
                continue

            data = self.dma_data[dma]
            assessment = self.assess_leakage_status(data['leakage_rate'])

            report.append(f"\n【分区 {dma}】")
            report.append("-" * 70)
            report.append(f"  总表读数：{data['total_flow']:.2f} m³")
            report.append(f"  用户表合计：{data['user_total']:.2f} m³")
            report.append(f"  漏损量：{data['leakage']:.2f} m³")
            report.append(f"  漏损率：{data['leakage_rate']:.2f}%")
            report.append(f"  状态等级：{assessment['level']}")
            report.append(f"  处置建议：{assessment['action']}")
            report.append(f"  紧急程度：{assessment['urgency']}")
            report.append("")

        # 汇总统计
        total_dmas = len(self.dma_data)
        if total_dmas > 0:
            avg_leakage_rate = statistics.mean([d['leakage_rate'] for d in self.dma_data.values()])
            total_leakage = sum([d['leakage'] for d in self.dma_data.values()])
            critical_count = sum([1 for d in self.dma_data.values() if d['leakage_rate'] >= 25])

            report.append("=" * 70)
            report.append("【汇总统计】")
            report.append(f"  分区数量：{total_dmas} 个")
            report.append(f"  平均漏损率：{avg_leakage_rate:.2f}%")
            report.append(f"  总漏损量：{total_leakage:.2f} m³")
            report.append(f"  严重分区数：{critical_count} 个")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def export_dma_report(self, output_file: str = "dma_leakage_report.json"):
        """导出DMA报告到JSON"""
        report_data = {
            'timestamp': str(__import__('datetime').datetime.now()),
            'dma_data': self.dma_data,
            'summary': {
                'total_dmas': len(self.dma_data),
                'avg_leakage_rate': round(statistics.mean([d['leakage_rate'] for d in self.dma_data.values()]), 2) if self.dma_data else 0,
                'total_leakage': round(sum([d['leakage'] for d in self.dma_data.values()]), 2) if self.dma_data else 0
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"DMA报告已导出到：{output_file}")


def main():
    """主函数 - 示例使用"""
    calc = LeakageCalculator()

    # 添加DMA数据
    calc.add_dma_data("DMA-001", 12500.5, [1200, 2500, 1800, 3200, 1500])
    calc.add_dma_data("DMA-002", 8200.3, [900, 1800, 1200, 2100, 800])
    calc.add_dma_data("DMA-003", 15600.8, [1500, 2800, 2200, 3500, 2000])

    # MNF分析
    flow_data = [
        {"time": "00:00", "flow": 180.5},
        {"time": "00:30", "flow": 175.2},
        {"time": "01:00", "flow": 170.8},
        {"time": "01:30", "flow": 168.5},
        {"time": "02:00", "flow": 165.2},
        {"time": "02:30", "flow": 164.8},
        {"time": "03:00", "flow": 166.5},
        {"time": "03:30", "flow": 168.2},
        {"time": "04:00", "flow": 172.5},
        {"time": "04:30", "flow": 180.8},
    ]

    mnf_result = calc.calculate_mnf(flow_data)
    print("\n【MNF分析结果】")
    print(f"  夜间最小流量：{mnf_result['mnf']} m³/h")
    print(f"  分析时段均值：{mnf_result['avg_flow']} m³/h")
    print(f"  数据点数：{mnf_result['data_points']}")
    print("")

    # 压力异常检测
    pressure_data = [
        {"time": "08:00", "pressure": 0.48},
        {"time": "09:00", "pressure": 0.47},
        {"time": "10:00", "pressure": 0.32},  # 异常低压
        {"time": "11:00", "pressure": 0.46},
        {"time": "12:00", "pressure": 0.47},
    ]

    pressure_result = calc.detect_pressure_anomaly(pressure_data)
    print("【压力异常检测】")
    print(f"  平均压力：{pressure_result['avg_pressure']} MPa")
    print(f"  异常点数：{pressure_result['anomaly_count']}")
    if pressure_result['anomalies']:
        print("  异常详情：")
        for anom in pressure_result['anomalies']:
            print(f"    {anom['time']} - {anom['type']} ({anom['deviation']}%)")
    print("")

    # 生成DMA报告
    print(calc.generate_dma_report())

    # 导出报告
    calc.export_dma_report("dma_leakage_report.json")


if __name__ == "__main__":
    main()
