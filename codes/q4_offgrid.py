import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, HOURS, FIG_DIR, TBL_DIR
from utils import (power_balance, calc_daily_energy, calc_green_indicators,
                   calc_electricity_cost, calc_generation_cost, calc_om_cost,
                   classify_scenario_indicators, generate_24_scenarios)
from visualization import (plot_offgrid_power_balance, plot_production_vs_curtailment,
                           plot_pareto_storage, plot_soc_discharge,
                           plot_offgrid_comparison, plot_net_vs_offgrid_comparison,
                           save_fig)

def offgrid_without_storage(P_wind, P_pv, P_conv, cfg, P_prod_max, P_prod_min):
    T = 24
    p_prod = np.zeros(T)
    P_curtail = np.zeros(T)

    for t in range(T):
        avail = P_wind[t] + P_pv[t] - P_conv[t]
        if avail >= P_prod_max:
            p_prod[t] = P_prod_max
            P_curtail[t] = avail - P_prod_max
        elif avail >= P_prod_min:
            p_prod[t] = avail
        elif avail > 0:
            p_prod[t] = 0
            P_curtail[t] = avail
        else:
            p_prod[t] = 0

    nh3_per_mwh = cfg.get_production_power(72)['nh3_rate_th'] / P_prod_max
    nh3_produced = np.sum(p_prod) * nh3_per_mwh
    total_curtail = np.sum(P_curtail)
    re_gen = np.sum(P_wind + P_pv)
    re_util = (re_gen - total_curtail) / re_gen if re_gen > 0 else 0

    return p_prod, P_curtail, nh3_produced, total_curtail, re_util

def offgrid_with_storage(P_wind, P_pv, P_conv, cfg, P_prod_max, P_prod_min,
                          storage_cap_MWh, storage_power_MW):
    T = 24
    p_prod = np.zeros(T)
    P_curtail = np.zeros(T)
    soc = np.zeros(T + 1)
    P_ch = np.zeros(T)
    P_dis = np.zeros(T)

    ch_eff = cfg.storage_ch_eff
    dis_eff = cfg.storage_dis_eff
    self_disch = cfg.storage_self_discharge
    soc[0] = storage_cap_MWh * 0.2

    for t in range(T):
        net_before = P_wind[t] + P_pv[t] - P_conv[t]

        if net_before >= P_prod_min:
            p_prod[t] = min(net_before, P_prod_max)
            leftover = net_before - p_prod[t]
            if leftover > 0 and soc[t] < storage_cap_MWh:
                ch_max = min(storage_power_MW, (storage_cap_MWh - soc[t]) / ch_eff)
                P_ch[t] = min(leftover, ch_max)
            if leftover - P_ch[t] > 0:
                P_curtail[t] = leftover - P_ch[t]
        else:
            needed = P_prod_min - net_before if net_before < P_prod_min else 0
            avail_dis = min(storage_power_MW, soc[t] * dis_eff)
            P_dis[t] = min(needed, avail_dis) if net_before < 0 else 0

            if net_before <= 0 and net_before + P_dis[t] >= 0:
                p_prod[t] = min(P_prod_max, P_dis[t] + net_before)
                if p_prod[t] < P_prod_min:
                    p_prod[t] = 0
            elif net_before > 0 and net_before < P_prod_min:
                p_prod[t] = 0
                leftover = net_before
                if soc[t] < storage_cap_MWh:
                    ch_max = min(storage_power_MW, (storage_cap_MWh - soc[t]) / ch_eff)
                    P_ch[t] = min(leftover, ch_max)
                if leftover - P_ch[t] > 0:
                    P_curtail[t] = leftover - P_ch[t]

        soc[t + 1] = min(storage_cap_MWh,
                         soc[t] * (1 - self_disch) + P_ch[t] * ch_eff - P_dis[t] / dis_eff)
        soc[t + 1] = max(0, soc[t + 1])

    nh3_per_mwh = cfg.get_production_power(72)['nh3_rate_th'] / P_prod_max
    nh3_produced = np.sum(p_prod) * nh3_per_mwh
    total_curtail = np.sum(P_curtail)
    re_gen = np.sum(P_wind + P_pv)
    re_util = (re_gen - total_curtail) / re_gen if re_gen > 0 else 0

    return p_prod, P_curtail, soc, P_ch, P_dis, nh3_produced, total_curtail, re_util

def calc_offgrid_cost(nh3_produced, cfg, capacity_tpd=72, P_wind_actual=None, P_pv_actual=None):
    if P_wind_actual is not None and P_pv_actual is not None:
        gen_cost = np.sum(P_wind_actual) * cfg.wind_cost + np.sum(P_pv_actual) * cfg.pv_cost
    else:
        gen_cost = calc_generation_cost(cfg)
    om_cost = calc_om_cost(nh3_produced, cfg, capacity_tpd)

    total_cost = gen_cost + om_cost
    cost_per_ton = total_cost / nh3_produced if nh3_produced > 0 else 0
    return total_cost, cost_per_ton, gen_cost, om_cost, 0

def run_q4():
    cfg = Config()
    scenarios = generate_24_scenarios(cfg)
    prod_cfg = cfg.get_production_power(72)
    P_prod_max = prod_cfg['total']
    P_prod_min = P_prod_max * 0.1

    print('=' * 70)
    print('问题四：离网运行分析及储能配置研究')
    print('=' * 70)

    print('\n--- 4.1 离网无储能运行 ---\n')
    q4_1_results = []
    for scen in scenarios:
        p_prod, P_curtail, nh3_prod, total_curt, re_util = offgrid_without_storage(
            scen['P_wind'], scen['P_pv'], cfg.P_conv, cfg, P_prod_max, P_prod_min)
        total_cost, cost_per_ton, _, _, _ = calc_offgrid_cost(
            nh3_prod, cfg, P_wind_actual=scen['P_wind'], P_pv_actual=scen['P_pv'])
        avail_energy = np.sum(scen['P_wind'] + scen['P_pv'] - cfg.P_conv)
        self_suff = nh3_prod * (cfg.get_production_power(72)['nh3_rate_th'] / P_prod_max) / np.maximum(1, np.sum(p_prod > 0))
        energy_self_suff = (np.sum(scen['P_wind'] + scen['P_pv']) - total_curt) / np.sum(scen['P_wind'] + scen['P_pv']) if np.sum(scen['P_wind'] + scen['P_pv']) > 0 else 0

        q4_1_results.append({
            'scenario': scen,
            'p_prod': p_prod,
            'P_curtail': P_curtail,
            'nh3_produced': nh3_prod,
            'total_curtail': total_curt,
            're_util': re_util,
            'cost_per_ton': cost_per_ton,
            'total_cost': total_cost,
            'self_suff': self_suff,
            'energy_self_suff': energy_self_suff,
        })

    total_annual_nh3 = sum(r['nh3_produced'] for r in q4_1_results) * cfg.days_per_scenario
    avg_cost = np.mean([r['cost_per_ton'] for r in q4_1_results if r['cost_per_ton'] > 0])
    avg_util = np.mean([r['nh3_produced'] / 72.0 for r in q4_1_results])
    avg_re_util = np.mean([r['re_util'] for r in q4_1_results])

    print(f'  全年制氨总量: {total_annual_nh3:.0f} 吨')
    print(f'  平均吨氨成本: {avg_cost:.0f} 元/吨')
    print(f'  平均产能利用率: {avg_util:.1%}')
    print(f'  平均可再生利用率: {avg_re_util:.1%}')

    max_curtail_scenario = max(q4_1_results, key=lambda r: r['total_curtail'])
    min_wind_scenario = min(q4_1_results, key=lambda r: r['nh3_produced'])

    print(f'\n  最大弃电场景: {max_curtail_scenario["scenario"]["label"]}, '
          f'弃电: {max_curtail_scenario["total_curtail"]:.1f} MWh')
    print(f'  最小产量场景: {min_wind_scenario["scenario"]["label"]}, '
          f'产量: {min_wind_scenario["nh3_produced"]:.1f} t')

    print('\n--- 4.2 储能配置优化 ---\n')
    storage_caps = np.arange(0, 201, 20)
    storage_power = 20
    best_storage_cap = 0
    best_avg_cost = float('inf')

    pareto_costs = []
    pareto_curtails = []

    for s_cap in storage_caps:
        scenario_costs = []
        scenario_curtails = []
        for scen in scenarios:
            p_prod, P_curtail, soc, P_ch, P_dis, nh3_prod, total_curt, re_util = \
                offgrid_with_storage(scen['P_wind'], scen['P_pv'], cfg.P_conv,
                                     cfg, P_prod_max, P_prod_min, s_cap, storage_power)
            total_cost, cost_per_ton, _, _, _ = calc_offgrid_cost(
                nh3_prod, cfg, P_wind_actual=scen['P_wind'], P_pv_actual=scen['P_pv'])

            if s_cap > 0:
                storage_inv = s_cap * 1000 * cfg.storage_inv / (cfg.storage_life * 365)
                storage_om = s_cap * cfg.storage_om
                total_cost += storage_inv + storage_om
                cost_per_ton = total_cost / nh3_prod if nh3_prod > 0 else 0

            scenario_costs.append(cost_per_ton)
            scenario_curtails.append(total_curt / max(1, np.sum(scen['P_wind'] + scen['P_pv'])))

        avg_scenario_cost = np.mean([c for c in scenario_costs if c > 0])
        avg_curtail = np.mean(scenario_curtails)

        pareto_costs.append(avg_scenario_cost)
        pareto_curtails.append(avg_curtail)

        if avg_scenario_cost < best_avg_cost:
            best_avg_cost = avg_scenario_cost
            best_storage_cap = s_cap

    print(f'  最优储能容量: {best_storage_cap:.0f} MWh')
    print(f'  最优下平均吨氨成本: {best_avg_cost:.0f} 元/吨')

    q4_2_storage_results = []
    for scen in scenarios:
        p_prod, P_curtail, soc, P_ch, P_dis, nh3_prod, total_curt, re_util = \
            offgrid_with_storage(scen['P_wind'], scen['P_pv'], cfg.P_conv,
                                 cfg, P_prod_max, P_prod_min,
                                 best_storage_cap, storage_power)
        total_cost, cost_per_ton, _, _, _ = calc_offgrid_cost(
            nh3_prod, cfg, P_wind_actual=scen['P_wind'], P_pv_actual=scen['P_pv'])
        storage_inv = best_storage_cap * 1000 * cfg.storage_inv / (cfg.storage_life * 365) if best_storage_cap > 0 else 0
        storage_om = best_storage_cap * cfg.storage_om
        total_cost += storage_inv + storage_om
        cost_per_ton = total_cost / nh3_prod if nh3_prod > 0 else 0

        re_gen_total = np.sum(scen['P_wind'] + scen['P_pv'])
        energy_self_suff = (re_gen_total - total_curt) / re_gen_total if re_gen_total > 0 else 0
        q4_2_storage_results.append({
            'scenario': scen,
            'p_prod': p_prod,
            'P_curtail': P_curtail,
            'soc': soc,
            'P_ch': P_ch,
            'P_dis': P_dis,
            'nh3_produced': nh3_prod,
            'total_curtail': total_curt,
            're_util': re_util,
            'energy_self_suff': energy_self_suff,
            'cost_per_ton': cost_per_ton,
        })

    total_annual_nh3_s = sum(r['nh3_produced'] for r in q4_2_storage_results) * cfg.days_per_scenario
    avg_cost_s = np.mean([r['cost_per_ton'] for r in q4_2_storage_results if r['cost_per_ton'] > 0])
    avg_util_s = np.mean([r['nh3_produced'] / 72.0 for r in q4_2_storage_results])

    print(f'\n  有储能全年制氨总量: {total_annual_nh3_s:.0f} 吨')
    print(f'  有储水平均吨氨成本: {avg_cost_s:.0f} 元/吨')
    print(f'  有储水平均产能利用率: {avg_util_s:.1%}')

    print('\n--- 4.3 离网 vs 联网经济性对比 ---\n')

    from q3_continuous import analyze_continuous_production as q3_func
    q3_annual_total = 0
    q3_costs = []
    q3_re_utils = []
    for i, scen in enumerate(scenarios):
        offgrid_nh3 = q4_1_results[i]['nh3_produced']
        target = max(offgrid_nh3, 0.1)
        res = q3_func(cfg, scen, target)
        actual_gen_cost = (np.sum(scen['P_wind']) * cfg.wind_cost +
                           np.sum(scen['P_pv']) * cfg.pv_cost)
        res['total_cost'] = res['total_cost'] - res['gen_cost'] + actual_gen_cost
        res['gen_cost'] = actual_gen_cost
        res['cost_per_ton'] = res['total_cost'] / res['nh3_production'] if res['nh3_production'] > 0 else 0
        q3_annual_total += res['nh3_production'] * cfg.days_per_scenario
        q3_costs.append(res['cost_per_ton'])
        if res['E_re'] > 0:
            q3_re_utils.append(1 - res['E_sell'] / res['E_re'])
        else:
            q3_re_utils.append(0)
    q3_avg_cost = np.mean(q3_costs) if q3_costs else 0
    q3_re_util = np.mean(q3_re_utils) if q3_re_utils else 0

    comparison_data = {
        'offgrid': {
            '吨氨成本': avg_cost,
            '净电费': avg_cost * total_annual_nh3 / 360,
            '年产量': total_annual_nh3,
            '能自给率': avg_re_util,
        },
        'offgrid_storage': {
            '吨氨成本': avg_cost_s if best_storage_cap > 0 else avg_cost,
            '净电费': (avg_cost_s if best_storage_cap > 0 else avg_cost) * (total_annual_nh3_s if best_storage_cap > 0 else total_annual_nh3) / 360,
            '年产量': total_annual_nh3_s if best_storage_cap > 0 else total_annual_nh3,
            '能自给率': np.mean([r['energy_self_suff'] for r in q4_2_storage_results]),
        },
        'ongrid': {
            '吨氨成本': q3_avg_cost,
            '净电费': q3_avg_cost * q3_annual_total / 360,
            '年产量': q3_annual_total,
            '能自给率': q3_re_util,
        },
    }

    print(f'  无储能离网: {avg_cost:.0f} 元/吨, {total_annual_nh3:.0f} 吨/年')
    print(f'  有储能离网: {avg_cost_s:.0f} 元/吨, {total_annual_nh3_s:.0f} 吨/年')
    print(f'  产量提升: {(total_annual_nh3_s/total_annual_nh3-1)*100:.1f}%')
    print(f'  联网对比(同等产量): {q3_avg_cost:.0f} 元/吨, {q3_annual_total:.0f} 吨/年')

    return {
        'q4_1_results': q4_1_results,
        'q4_2_results': q4_2_storage_results,
        'best_storage_cap': best_storage_cap,
        'pareto_costs': pareto_costs,
        'pareto_curtails': pareto_curtails,
        'storage_caps': storage_caps.tolist(),
        'comparison': comparison_data,
        'scenarios': scenarios,
    }

def plot_q4_results(q4_data, cfg):
    scenarios = q4_data['scenarios']
    q4_1 = q4_data['q4_1_results']

    max_curtail = max(q4_1, key=lambda r: r['total_curtail'])
    fig13 = plot_offgrid_power_balance(
        HOURS, max_curtail['scenario']['P_wind'], max_curtail['scenario']['P_pv'],
        cfg.P_conv, max_curtail['p_prod'], max_curtail['P_curtail'],
        title=f'离网运行功率平衡（{max_curtail["scenario"]["label"]}）')
    save_fig(fig13, 'fig13_offgrid_power_balance.pdf', 'q4')

    labels = [s['label'] for s in scenarios]
    prods = [r['nh3_produced'] for r in q4_1]
    curtails = [r['total_curtail'] / max(1, np.sum(s['P_wind'] + s['P_pv']))
                for s, r in zip(scenarios, q4_1)]
    fig14 = plot_production_vs_curtailment(
        labels, prods, curtails,
        title='各场景产量与弃电分析（离网无储能）')
    save_fig(fig14, 'fig14_production_curtail.pdf', 'q4')

    fig15 = plot_pareto_storage(
        q4_data['storage_caps'], q4_data['pareto_costs'],
        q4_data['pareto_curtails'],
        title='储能容量优化Pareto曲线')
    save_fig(fig15, 'fig15_pareto_storage.pdf', 'q4')

    if q4_data['best_storage_cap'] > 0:
        rep_scenarios = [q4_1[0], q4_1[6], q4_1[12]]
        soc_data = {}
        for rs in rep_scenarios:
            label = rs['scenario']['label']
            for q4_2_r in q4_data['q4_2_results']:
                if q4_2_r['scenario']['id'] == rs['scenario']['id']:
                    soc_data[label] = q4_2_r['soc'][:-1] / q4_data['best_storage_cap'] * 100
                    break
        if soc_data:
            rep_q4_2 = [r for r in q4_data['q4_2_results'] if r['scenario']['id'] in [1, 7, 13]]
            fig16 = plot_soc_discharge(
                soc_data,
                rep_q4_2[0]['P_ch'] if rep_q4_2 else np.zeros(24),
                rep_q4_2[0]['P_dis'] if rep_q4_2 else np.zeros(24),
                HOURS, title='储能SOC与充放电功率（典型场景）')
            save_fig(fig16, 'fig16_soc_discharge.pdf', 'q4')

    with_storage = {
        'curtail_rates': [r['total_curtail'] / max(1, np.sum(r['scenario']['P_wind'] + r['scenario']['P_pv']))
                         for r in q4_data['q4_2_results']],
        'productions': [r['nh3_produced'] for r in q4_data['q4_2_results']],
        'util_rates': [r['nh3_produced'] / 72.0 for r in q4_data['q4_2_results']],
        're_util_rates': [r['re_util'] for r in q4_data['q4_2_results']],
    }
    without_storage = {
        'curtail_rates': [r['total_curtail'] / max(1, np.sum(r['scenario']['P_wind'] + r['scenario']['P_pv']))
                         for r in q4_1],
        'productions': [r['nh3_produced'] for r in q4_1],
        'util_rates': [r['nh3_produced'] / 72.0 for r in q4_1],
        're_util_rates': [r['re_util'] for r in q4_1],
    }
    fig17 = plot_offgrid_comparison(
        scenarios, with_storage, without_storage,
        title='离网运行有无储能对比')
    save_fig(fig17, 'fig17_storage_comparison.pdf', 'q4')

    fig18 = plot_net_vs_offgrid_comparison(
        q4_data['comparison'],
        title='离网与联网模式经济性对比')
    save_fig(fig18, 'fig18_net_vs_offgrid.pdf', 'q4')

if __name__ == '__main__':
    cfg = Config()
    q4_data = run_q4()
    plot_q4_results(q4_data, cfg)
    print('\nQ4 figures saved.')
