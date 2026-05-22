import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, HOURS, FIG_DIR, TBL_DIR
from utils import (power_balance, calc_daily_energy, calc_green_indicators,
                   calc_electricity_cost, calc_ammonia_cost, calc_generation_cost,
                   calc_om_cost, classify_scenario_indicators,
                   generate_24_scenarios, level_to_capacity)
from visualization import (plot_gantt_chart, plot_cost_vs_production,
                           plot_24_scenarios_heatmap, plot_scenario_compliance,
                           plot_annual_cost_distribution, save_fig)

def optimize_schedule(P_wind, P_pv, P_conv, P_prod, cfg, k_hours):
    T = 24
    marginal_costs = np.zeros(T)
    om_hourly = (cfg.alkel_om * 20 + cfg.pemel_om * 20 + cfg.nh3_om * 1.5)

    for t in range(T):
        net_off = P_wind[t] + P_pv[t] - P_conv[t]
        if net_off >= 0:
            cost_off = -net_off * cfg.price_sell
        else:
            cost_off = -net_off * cfg.price_buy[t]

        net_on = net_off - P_prod
        if net_on >= 0:
            cost_on = -net_on * cfg.price_sell
        else:
            cost_on = -net_on * cfg.price_buy[t]

        marginal_costs[t] = cost_on + om_hourly - cost_off

    sorted_idx = np.argsort(marginal_costs)
    selected = np.zeros(T, dtype=bool)
    selected[sorted_idx[:k_hours]] = True

    P_prod_sched = np.where(selected, P_prod, 0.0)
    P_buy, P_sell, P_re = power_balance(P_wind, P_pv, P_conv, P_prod_sched)

    return selected, P_buy, P_sell, marginal_costs

def analyze_production_level(cfg, scenario, target_tpd, installed_capacity=72):
    k_hours = int(round(target_tpd / installed_capacity * 24))
    if k_hours == 0:
        return None

    prod = cfg.get_production_power(installed_capacity)
    P_prod = prod['total']
    nh3_rate = prod['nh3_rate_th']

    P_wind = scenario['P_wind']
    P_pv = scenario['P_pv']
    P_conv = cfg.P_conv

    selected, P_buy, P_sell, _ = optimize_schedule(
        P_wind, P_pv, P_conv, P_prod, cfg, k_hours)

    P_prod_sched = np.where(selected, P_prod, 0.0)
    E_re, E_total, E_sell, E_buy, E_self = calc_daily_energy(
        P_wind, P_pv, P_conv, P_prod_sched, P_buy, P_sell)

    indicators = calc_green_indicators(E_re, E_total, E_sell, E_buy, cfg)

    net_elec_cost = calc_electricity_cost(P_buy, P_sell, cfg.price_buy, cfg.price_sell)
    gen_cost = calc_generation_cost(cfg)

    hours_run = np.sum(selected)
    nh3_production = hours_run * nh3_rate

    om_cost = calc_om_cost(nh3_production, cfg, installed_capacity)

    total_cost = net_elec_cost + gen_cost + om_cost
    cost_per_ton = total_cost / nh3_production if nh3_production > 0 else 0
    util_rate = hours_run / 24.0

    return {
        'capacity': target_tpd,
        'installed_capacity': installed_capacity,
        'nh3_production': nh3_production,
        'hours_run': hours_run,
        'selected': selected,
        'indicators': indicators,
        'net_elec_cost': net_elec_cost,
        'gen_cost': gen_cost,
        'om_cost': om_cost,
        'dep_cost': 0,
        'total_cost': total_cost,
        'cost_per_ton': cost_per_ton,
        'utilization_rate': util_rate,
        'E_re': E_re, 'E_total': E_total, 'E_sell': E_sell, 'E_buy': E_buy,
        'P_buy': P_buy, 'P_sell': P_sell,
        'classification': classify_scenario_indicators(indicators),
    }

def run_q2():
    cfg = Config()
    production_levels = [72, 63, 54, 45, 36]
    scenarios = generate_24_scenarios(cfg)
    typical_scenario = {
        'P_wind': cfg.P_wind_typ,
        'P_pv': cfg.P_pv_typ,
        'label': '典型',
    }

    print('=' * 70)
    print('问题二：基于离散制氨调节的绿电直连型电氢氨园区运行优化')
    print('=' * 70)

    print('\n--- 2.1 典型风光场景分析 ---\n')
    typical_results = {}
    sched_data = []
    for cap in production_levels:
        res = analyze_production_level(cfg, typical_scenario, cap)
        typical_results[cap] = res
        sched_data.append(res['selected'])
        ind = res['indicators']
        status = '✓' if ind['all_pass'] else '✗'
        print(f'  产量 {cap:2d} t/d | 运行 {res["hours_run"]:2d}h | '
              f'吨氨成本 {res["cost_per_ton"]:8.0f} 元 | '
              f'自用 {ind["self_consume_ratio"]:.1%}/{ind["green_ratio"]:.1%}/{ind["curtail_ratio"]:.1%} | {status}')

    min_cost = min(typical_results.values(), key=lambda r: r['cost_per_ton'])
    print(f'\n  最优产量: {min_cost["capacity"]} t/d, '
          f'吨氨成本: {min_cost["cost_per_ton"]:.0f} 元/吨')

    print(f'\n--- 2.2 24种风光场景分析 ---\n')
    all_results = {}
    for cap in production_levels:
        all_results[cap] = []

    for scen in scenarios:
        for cap in production_levels:
            res = analyze_production_level(cfg, scen, cap)
            if res:
                all_results[cap].append(res)

    compliance_counts = {}
    for cap in production_levels:
        counts = {'all_pass': 0, 'partial_pass': 0, 'no_pass': 0}
        for r in all_results[cap]:
            counts[r['classification']] += 1
        compliance_counts[cap] = counts

    print(f'  {"产量":>8s} | {"全满足":>8s} | {"部分满足":>8s} | {"全不满足":>8s}')
    print(f'  {"-"*8}-+-{"-"*8}-+-{"-"*8}-+-{"-"*8}')
    for cap in production_levels:
        c = compliance_counts[cap]
        print(f'  {cap:5d} t/d | {c["all_pass"]:6d}   | {c["partial_pass"]:6d}   | {c["no_pass"]:6d}')

    annual_costs = {}
    for cap in production_levels:
        costs = [r['cost_per_ton'] for r in all_results[cap] if r['cost_per_ton'] > 0]
        annual_costs[cap] = costs

    annual_total_cost = {}
    for cap in production_levels:
        total = sum(r['nh3_production'] * r['cost_per_ton'] for r in all_results[cap])
        annual_total_cost[cap] = total

    return {
        'typical_results': typical_results,
        'all_results': all_results,
        'compliance_counts': compliance_counts,
        'annual_costs': annual_costs,
        'annual_total_cost': annual_total_cost,
        'production_levels': production_levels,
        'scenarios': scenarios,
        'sched_data': sched_data,
    }

def plot_q2_results(q2_data, cfg):
    levels = q2_data['production_levels']
    typ_results = q2_data['typical_results']
    scenarios = q2_data['scenarios']
    all_results = q2_data['all_results']
    compliance_counts = q2_data['compliance_counts']

    fig4 = plot_gantt_chart(
        cfg, [q2_data['sched_data'][i] for i in range(len(levels))],
        levels, title='各产量最优生产时段安排（典型场景）')
    save_fig(fig4, 'fig4_gantt.pdf', 'q2')

    fig5 = plot_cost_vs_production(
        levels, [typ_results[l] for l in levels],
        title='关键指标随产量变化（典型场景）')
    save_fig(fig5, 'fig5_cost_vs_production.pdf', 'q2')

    scenario_ids = [s['label'] for s in scenarios]
    cost_matrix = np.zeros((len(scenarios), len(levels)))
    for i in range(len(scenarios)):
        for j, l in enumerate(levels):
            if i < len(all_results[l]):
                cost_matrix[i, j] = all_results[l][i]['cost_per_ton']
    fig6 = plot_24_scenarios_heatmap(
        scenario_ids, levels, cost_matrix,
        title='24场景×5产量吨氨成本热力图')
    save_fig(fig6, 'fig6_heatmap.pdf', 'q2')

    fig7 = plot_scenario_compliance(
        compliance_counts, levels,
        title='各产量绿电指标达标统计（24场景）')
    save_fig(fig7, 'fig7_compliance.pdf', 'q2')

    fig8 = plot_annual_cost_distribution(
        q2_data['annual_costs'], levels,
        title='全年吨氨成本分布曲线（离散调节）')
    save_fig(fig8, 'fig8_annual_cost_distribution.pdf', 'q2')

if __name__ == '__main__':
    cfg = Config()
    q2_data = run_q2()
    plot_q2_results(q2_data, cfg)
    print('\nQ2 figures saved.')
