import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, HOURS, FIG_DIR, TBL_DIR
from utils import (power_balance, calc_daily_energy, calc_green_indicators,
                   calc_electricity_cost, calc_generation_cost, calc_om_cost,
                   classify_scenario_indicators, generate_24_scenarios,
                   level_to_capacity)
from visualization import (plot_q3_power_schedule, plot_comparison_q2_q3,
                           plot_compliance_comparison, plot_annual_cost_distribution,
                           save_fig)

def optimize_continuous(P_wind, P_pv, P_conv, cfg, target_nh3_t, P_max, P_min_ratio=0.1):
    T = 24
    prod_cfg = cfg.get_production_power(72)
    P_prod_max = prod_cfg['total']
    P_prod_min = P_prod_max * P_min_ratio
    nh3_per_mwh = prod_cfg['nh3_rate_th'] / P_prod_max
    total_energy_needed = target_nh3_t / nh3_per_mwh
    om_per_mwh = (cfg.alkel_om * 0.5 + cfg.pemel_om * 0.5 + cfg.nh3_om * 0.5)

    net_avail = P_wind + P_pv - P_conv

    p_opt = np.zeros(T)
    remaining = total_energy_needed

    surplus_hours = np.argsort(-net_avail)
    for t in surplus_hours:
        if remaining <= 0:
            break
        if net_avail[t] <= 0:
            break
        use = min(remaining, net_avail[t], P_prod_max)
        if use >= P_prod_min or (use > 0 and remaining <= use):
            p_opt[t] = use
            remaining -= use

    if remaining > 0:
        class HourCost:
            def __init__(self, idx, net):
                self.idx = idx
                if net >= 0:
                    self.cost = -cfg.price_sell + om_per_mwh
                else:
                    self.cost = cfg.price_buy[idx] + om_per_mwh
                self.avail = P_prod_max - p_opt[idx]

        sorted_hours = sorted([HourCost(t, net_avail[t]) for t in range(T)],
                              key=lambda h: h.cost)

        for h in sorted_hours:
            if remaining <= 0:
                break
            add = min(remaining, h.avail)
            if add >= P_prod_min or p_opt[h.idx] > 0 or remaining >= P_prod_min:
                p_opt[h.idx] += add
                remaining -= add

    if remaining > 0.01:
        running_hours = [t for t in range(T) if p_opt[t] >= P_prod_min * 0.5]
        if running_hours:
            running_hours.sort(key=lambda t: P_prod_max - p_opt[t], reverse=True)
            for t in running_hours:
                if remaining <= 0.01:
                    break
                add = min(remaining, P_prod_max - p_opt[t])
                p_opt[t] += add
                remaining -= add

    if remaining > 0.01:
        candidates = [(t, P_prod_max - p_opt[t], net_avail[t]) for t in range(T)]
        candidates.sort(key=lambda x: -x[2])
        t, cap, _ = candidates[0]
        add = min(remaining, cap)
        p_opt[t] += add
        remaining -= add

    if remaining > 0.01:
        p_opt[np.argmax(P_prod_max - p_opt)] += remaining

    p_opt = np.clip(p_opt, 0, P_prod_max)
    running = p_opt >= P_prod_min * 0.5
    if np.any(p_opt > 0) and not np.any(running):
        max_idx = np.argmax(p_opt)
        running[max_idx] = True
    p_opt[~running] = 0

    nh3_produced = np.sum(p_opt) * nh3_per_mwh
    return p_opt, nh3_produced

def analyze_continuous_production(cfg, scenario, target_nh3, capacity_tpd=72):
    P_wind = scenario['P_wind']
    P_pv = scenario['P_pv']
    P_conv = cfg.P_conv
    prod_cfg = cfg.get_production_power(capacity_tpd)
    P_prod_max = prod_cfg['total']

    p_opt, nh3_produced = optimize_continuous(
        P_wind, P_pv, P_conv, cfg, target_nh3, P_prod_max)

    P_buy, P_sell, P_re = power_balance(P_wind, P_pv, P_conv, p_opt)
    E_re, E_total, E_sell, E_buy, E_self = calc_daily_energy(
        P_wind, P_pv, P_conv, p_opt, P_buy, P_sell)

    indicators = calc_green_indicators(E_re, E_total, E_sell, E_buy, cfg)
    net_elec_cost = calc_electricity_cost(P_buy, P_sell, cfg.price_buy, cfg.price_sell)
    gen_cost = calc_generation_cost(cfg)
    om_cost = calc_om_cost(nh3_produced, cfg, capacity_tpd)

    total_cost = net_elec_cost + gen_cost + om_cost
    cost_per_ton = total_cost / nh3_produced if nh3_produced > 0 else 0

    return {
        'capacity': target_nh3,
        'nh3_production': nh3_produced,
        'p_opt': p_opt,
        'indicators': indicators,
        'net_elec_cost': net_elec_cost,
        'gen_cost': gen_cost,
        'om_cost': om_cost,
        'dep_cost': 0,
        'total_cost': total_cost,
        'cost_per_ton': cost_per_ton,
        'E_re': E_re, 'E_total': E_total, 'E_sell': E_sell, 'E_buy': E_buy,
        'P_buy': P_buy, 'P_sell': P_sell,
        'classification': classify_scenario_indicators(indicators),
    }

def run_q3():
    cfg = Config()
    production_levels = [72, 63, 54, 45, 36]
    scenarios = generate_24_scenarios(cfg)

    typical_scenario = {
        'P_wind': cfg.P_wind_typ,
        'P_pv': cfg.P_pv_typ,
    }

    print('=' * 70)
    print('问题三：连续调节制氨优化结果')
    print('=' * 70)

    print('\n--- 典型场景连续调节结果 ---')
    q3_typical = {}
    for cap in production_levels:
        res = analyze_continuous_production(cfg, typical_scenario, cap)
        q3_typical[cap] = res
        ind = res['indicators']
        print(f'  目标 {cap:2d} t/d | 实产 {res["nh3_production"]:.1f} t | '
              f'成本 {res["cost_per_ton"]:8.0f} 元 | '
              f'自用/绿电/上网 {ind["self_consume_ratio"]:.1%}/{ind["green_ratio"]:.1%}/{ind["curtail_ratio"]:.1%}')

    print('\n--- 24场景分析 ---')
    q3_scenario = {}
    for cap in production_levels:
        q3_scenario[cap] = []
        for scen in scenarios:
            res = analyze_continuous_production(cfg, scen, cap)
            if res and res['nh3_production'] > 0:
                q3_scenario[cap].append(res)

    compliance_counts = {}
    for cap in production_levels:
        counts = {'all_pass': 0, 'partial_pass': 0, 'no_pass': 0}
        for r in q3_scenario[cap]:
            counts[r['classification']] += 1
        compliance_counts[cap] = counts

    print(f'  {"目标产量":>8s} | {"全满足":>8s} | {"部分满足":>8s} | {"全不满足":>8s}')
    for cap in production_levels:
        c = compliance_counts[cap]
        print(f'  {cap:5d} t/d | {c["all_pass"]:6d}   | {c["partial_pass"]:6d}   | {c["no_pass"]:6d}')

    annual_costs = {}
    for cap in production_levels:
        costs = [r['cost_per_ton'] for r in q3_scenario[cap] if r['cost_per_ton'] > 0]
        annual_costs[cap] = costs

    return {
        'q3_typical': q3_typical,
        'q3_scenario': q3_scenario,
        'compliance_counts': compliance_counts,
        'annual_costs': annual_costs,
        'production_levels': production_levels,
        'scenarios': scenarios,
        'typical_scenario': typical_scenario,
    }

def plot_q3_results(q3_data, cfg, q2_data=None):
    levels = q3_data['production_levels']
    typ_results = q3_data['q3_typical']

    first_cap = levels[0]
    first_res = typ_results[first_cap]
    if first_res:
        P_wind = cfg.P_wind_typ if 'P_wind' in q3_data['typical_scenario'] else cfg.P_wind_typ
        P_pv = cfg.P_pv_typ
        plot_input_data = {
            'P_wind': P_wind,
            'P_pv': P_pv,
            'P_conv': cfg.P_conv,
            'P_prod_continuous': first_res['p_opt'],
            'P_prod_discrete': q2_data['sched_data'][0] * cfg.get_production_power(levels[0])['total'] if q2_data else np.zeros(24),
            'P_buy': first_res.get('P_buy', np.zeros(24)),
            'P_sell': first_res.get('P_sell', np.zeros(24)),
        }

        sched = q2_data['sched_data'][0] if q2_data else np.zeros(24, dtype=bool)
        prod_power = cfg.get_production_power(levels[0])['total']
        fig9 = plot_q3_power_schedule(
            HOURS, plot_input_data['P_wind'], plot_input_data['P_pv'],
            plot_input_data['P_conv'], plot_input_data['P_prod_continuous'],
            sched * prod_power, plot_input_data['P_buy'], plot_input_data['P_sell'],
            title=f'连续调节功率调度方案（{levels[0]} t/d 典型场景）')
        save_fig(fig9, 'fig9_q3_power_schedule.pdf', 'q3')

    if q2_data:
        q3_costs = [typ_results[l]['cost_per_ton'] for l in levels]
        q2_costs = [q2_data['typical_results'][l]['cost_per_ton'] for l in levels]
        q3_inds = {l: typ_results[l]['indicators'] for l in levels}
        q2_inds = {l: q2_data['typical_results'][l]['indicators'] for l in levels}

        fig10 = plot_comparison_q2_q3(
            levels, q2_costs, q3_costs, q2_inds, q3_inds,
            title='Q2 vs Q3 吨氨成本与绿电指标对比（典型场景）')
        save_fig(fig10, 'fig10_q2_vs_q3.pdf', 'q3')

        fig11 = plot_annual_cost_distribution(
            q3_data['annual_costs'], levels,
            title='全年吨氨成本分布曲线（连续调节）')
        save_fig(fig11, 'fig11_q3_annual_distribution.pdf', 'q3')

        fig12 = plot_compliance_comparison(
            levels, q2_data['compliance_counts'], q3_data['compliance_counts'],
            title='Q2 vs Q3 绿电指标达标统计对比')
        save_fig(fig12, 'fig12_q3_vs_q2_compliance.pdf', 'q3')

if __name__ == '__main__':
    cfg = Config()
    q3_data = run_q3()
    try:
        from q2_scheduling import run_q2
        q2_data = run_q2()
        plot_q3_results(q3_data, cfg, q2_data)
    except:
        plot_q3_results(q3_data, cfg)
    print('\nQ3 figures saved.')
