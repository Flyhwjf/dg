import numpy as np
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, FIG_DIR
from visualization import plot_policy_analysis, save_fig

def generate_policy_data():
    cfg = Config()

    policy_data = {
        'negative_impacts': [
            {
                'title': '调峰压力显著增大',
                'severity': 0.85,
                'description': (
                    '绿电园区高渗透率下，风电、光伏的间歇性和波动性将直接传递至公共电网。'
                    '园区净负荷（总负荷-绿电出力）的随机波动幅度增大，'
                    '导致电网调峰机组需频繁启停和大幅调节出力。'
                    '以本园区为例，104MW新能源出力在0-104MW间波动，'
                    '日最大峰谷差可达80MW以上。'
                ),
                'data': {
                    'daily_peak_valley_MW': 85,
                    'ramp_rate_MWh': 45,
                }
            },
            {
                'title': '备用容量需求增加',
                'severity': 0.70,
                'description': (
                    '为应对绿电出力骤降（如云层遮挡导致光伏出力在10分钟内下降50%），'
                    '电力系统需预留更多旋转备用和冷备用容量。'
                    '研究表明，每增加10%可再生能源渗透率，系统备用容量需求增加3-5%。'
                    '这将推高电力系统的运行成本和容量费用。'
                ),
                'data': {
                    'reserve_increase_per_10pct_RE': 0.04,
                    'annual_reserve_cost_increase': 15000000,
                }
            },
            {
                'title': '电能质量与系统稳定性挑战',
                'severity': 0.60,
                'description': (
                    '大规模电力电子接口的新能源并网（逆变器、制氢电源等）'
                    '将降低系统惯量，增加频率和电压越限风险。'
                    '电解槽等非线性负荷会产生谐波污染，影响电能质量。'
                    '当绿电渗透率超过30%时，系统的短路容量和惯量水平显著下降。'
                ),
                'data': {
                    'max_RE_penetration_without_stability_issues': 0.30,
                    'inertia_decline_per_10pct_RE': 0.08,
                }
            },
        ],
        'positive_impacts': [
            {
                'title': '促进新能源就近消纳',
                'severity': 0.90,
                'description': (
                    '绿电直连园区通过"源网荷储"一体化模式，实现了新能源的就地消纳。'
                    '本园区中，72t/d产能时绿电自用比例达86.5%，'
                    '显著降低了新能源弃电率（6.7%），远低于全国平均弃风弃光率。'
                    '这种模式为高比例新能源消纳提供了可复制的示范路径。'
                ),
                'data': {
                    'self_consume_ratio': 0.865,
                    'curtailment_rate': 0.067,
                    'national_avg_curtailment': 0.15,
                }
            },
            {
                'title': '有效降低系统碳排放',
                'severity': 0.95,
                'description': (
                    '绿电制氢氨替代传统化石能源制氢氨，具有显著的碳减排效益。'
                    '每吨绿氨可减少CO₂排放约2.5吨（对比煤气化制氨）。'
                    '本园区满产年产量25920吨，年碳减排约64800吨CO₂。'
                    '同时，绿电直连模式减少了电网输配电损耗，进一步提升能效。'
                ),
                'data': {
                    'CO2_reduction_per_ton_nh3': 2.5,
                    'annual_CO2_reduction_tons': 64800,
                    'grid_loss_reduction': 0.03,
                }
            },
            {
                'title': '推动储能与氢能技术产业链发展',
                'severity': 0.75,
                'description': (
                    '绿电直连园区对储能的需求（平抑波动、削峰填谷）'
                    '将推动电池储能、氢储能等技术的规模化应用和成本下降。'
                    '同时，绿氢-绿氨产业链的建立将带动电解槽、'
                    '合成氨催化剂、储氢材料等相关产业的发展。'
                    '形成"新能源-氢能-化工"联动的绿色产业集群。'
                ),
                'data': {
                    'battery_cost_decline_annual': 0.10,
                    'electrolyzer_cost_decline_annual': 0.08,
                }
            },
        ],
        'policy_recommendations': [
            {
                'title': '完善绿电市场化交易机制',
                'priority': 0.92,
                'description': (
                    '建立绿电直连园区的电力市场化交易机制，'
                    '包括绿电证书交易、碳排放权交易等。'
                    '允许园区参与辅助服务市场（调频、备用），'
                    '通过市场化手段获取灵活性收益。'
                    '建议设立绿电园区专用交易通道，简化并网审批流程。'
                ),
            },
            {
                'title': '强制配套储能设施',
                'priority': 0.82,
                'description': (
                    '要求绿电直连园区按装机容量的10-20%配置储能，'
                    '用于平滑出力波动和提供系统支撑。'
                    '储能容量配置可作为并网的前置条件。'
                    '对储能投资给予税收减免或补贴（如投资补贴30%）。'
                    '推动"共享储能"模式，降低单一园区储能成本。'
                ),
            },
            {
                'title': '推广智能调度与预测技术',
                'priority': 0.75,
                'description': (
                    '应用风光功率预测、负荷预测、AI优化调度等技术，'
                    '实现园区与电网的协调运行。'
                    '建立园区级能量管理系统（EMS），'
                    '实现风光-制氢-储能-负荷的多时间尺度协调优化。'
                    '本研究表明，连续调节（Q3）相比离散调节（Q2）'
                    '可降低吨氨成本10-30%，提升绿电指标达标率。'
                ),
            },
            {
                'title': '实施差异化电价与补贴政策',
                'priority': 0.88,
                'description': (
                    '对绿电直连园区实行优惠的过网费政策，'
                    '降低"绿电-绿氢"产业链的综合用电成本。'
                    '对达到绿电指标要求的园区给予碳收益奖励。'
                    '设立绿电制氢氨专项基金，支持技术研发和示范项目。'
                ),
            },
            {
                'title': '加强技术研发与标准制定',
                'priority': 0.78,
                'description': (
                    '支持大功率电解槽、高效合成氨催化剂、'
                    '低成本储氢材料等核心技术攻关。'
                    '制定绿电直连园区规划设计、运行管理、'
                    '并网接入等系列技术标准。'
                    '建立绿氢-绿氨认证体系，打通国际市场准入。'
                ),
            },
        ],
        'quantitative_summary': {
            'capacity_factor_range': '37.7%-100%',
            'cost_range_yuan_per_ton': '3497-7435',
            'CO2_reduction_annual_tons': 64800,
            'RE_self_consumption_range': '82.4%-86.5%',
            'storage_capex_per_kWh': 1000,
            'recommended_storage_ratio': '10-20%',
        }
    }

    return policy_data

def plot_q5_results(save_dir=None):
    fig19 = plot_policy_analysis()
    path = save_fig(fig19, 'fig19_policy_analysis.pdf', 'q5')
    return path

def print_q5_summary():
    data = generate_policy_data()
    print('=' * 70)
    print('问题五：政策影响分析与建议')
    print('=' * 70)

    print('\n--- 不利影响 ---')
    for imp in data['negative_impacts']:
        print(f'  [{imp["severity"]:.0%}] {imp["title"]}')
        print(f'    {imp["description"][:80]}...')

    print('\n--- 有利影响 ---')
    for imp in data['positive_impacts']:
        print(f'  [{imp["severity"]:.0%}] {imp["title"]}')
        print(f'    {imp["description"][:80]}...')

    print('\n--- 政策建议（按优先级） ---')
    for rec in sorted(data['policy_recommendations'], key=lambda r: -r['priority']):
        print(f'  [{rec["priority"]:.0%}] {rec["title"]}')

    print('\n--- 关键数据汇总 ---')
    s = data['quantitative_summary']
    print(f'  产能利用率范围: {s["capacity_factor_range"]}')
    print(f'  吨氨成本范围: {s["cost_range_yuan_per_ton"]} 元/吨')
    print(f'  年碳减排量: {s["CO2_reduction_annual_tons"]} 吨CO₂')
    print(f'  绿电自用比例: {s["RE_self_consumption_range"]}')
    print('=' * 70)

if __name__ == '__main__':
    print_q5_summary()
    plot_q5_results()
    print('\nQ5 figure saved.')
