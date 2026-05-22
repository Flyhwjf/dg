import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, TIME_LABELS, FIG_DIR, TBL_DIR, HOURS
from utils import (power_balance, calc_daily_energy, calc_green_indicators,
                   calc_electricity_cost, calc_ammonia_cost, calc_generation_cost)
from visualization import (plot_power_balance, plot_green_indicators_radar,
                           plot_sankey_diagram, save_fig)

def run_q1():
    cfg = Config()
    Q_NH3 = 36.0
    prod = cfg.get_production_power(Q_NH3)
    P_prod = np.full(24, prod['total'])

    P_wind = cfg.P_wind_typ
    P_pv = cfg.P_pv_typ
    P_conv = cfg.P_conv

    P_buy, P_sell, P_re = power_balance(P_wind, P_pv, P_conv, P_prod)

    E_re, E_total, E_sell, E_buy, E_self = calc_daily_energy(
        P_wind, P_pv, P_conv, P_prod, P_buy, P_sell)

    indicators = calc_green_indicators(E_re, E_total, E_sell, E_buy, cfg)

    net_elec_cost = calc_electricity_cost(P_buy, P_sell, cfg.price_buy, cfg.price_sell)
    gen_cost = calc_generation_cost(cfg)
    total_cost, cost_per_ton = calc_ammonia_cost(
        net_elec_cost + gen_cost, Q_NH3, cfg, Q_NH3)

    results = {
        'P_wind': P_wind, 'P_pv': P_pv, 'P_conv': P_conv,
        'P_prod': P_prod, 'P_buy': P_buy, 'P_sell': P_sell,
        'E_re': E_re, 'E_total': E_total, 'E_sell': E_sell,
        'E_buy': E_buy, 'E_self': E_self,
        'indicators': indicators,
        'net_elec_cost': net_elec_cost,
        'gen_cost': gen_cost,
        'total_cost': total_cost,
        'cost_per_ton': cost_per_ton,
        'nh3_production': Q_NH3,
        'P_re': P_re,
    }

    return results

def plot_q1_results(results, cfg):
    fig1 = plot_power_balance(
        HOURS, results['P_wind'], results['P_pv'], results['P_conv'],
        results['P_buy'], results['P_sell'], results['P_prod'],
        title='园区典型日功率平衡曲线')
    save_fig(fig1, 'fig1_power_balance.pdf', 'q1')

    radar_data = {
        '自发自用比例': results['indicators']['self_consume_ratio'],
        '总用电绿电比例': results['indicators']['green_ratio'],
        '上网电量比例': results['indicators']['curtail_ratio'],
    }
    radar_req = {
        '自发自用比例': cfg.REQUIRE_SELF_CONSUME,
        '总用电绿电比例': cfg.REQUIRE_GREEN_RATIO,
        '上网电量比例': cfg.REQUIRE_CURTAIL_RATIO,
    }
    fig2 = plot_green_indicators_radar(
        radar_data, radar_req, title='绿电指标达标分析')
    save_fig(fig2, 'fig2_green_indicators_radar.pdf', 'q1')

    fig3 = plot_sankey_diagram(
        values=[results['E_re'] - results['E_sell'], results['E_sell'],
                results['E_buy'], results['E_self'], results['E_sell'] * 0.5, results['E_buy'] * 0.5],
        labels=['自用可再生', '上网电量', '网购电量', '制氢氨', '售电(收入)', '购电(支出)'],
        title='园区日能量流向')
    save_fig(fig3, 'fig3_sankey.pdf', 'q1')

def print_q1_results(results, cfg):
    ind = results['indicators']
    print('=' * 60)
    print('问题一：典型风光场景分析结果')
    print('=' * 60)
    print(f'新能源发电量:          {results["E_re"]:.2f} MWh')
    print(f'总用电量:              {results["E_total"]:.2f} MWh')
    print(f'上网电量:              {results["E_sell"]:.2f} MWh')
    print(f'网购电量:              {results["E_buy"]:.2f} MWh')
    print(f'新能源自发自用电量:    {results["E_self"]:.2f} MWh')
    print()
    print(f'自发自用比例:          {ind["self_consume_ratio"]:.2%}  (要求>60%) {"✓" if ind["self_consume_pass"] else "✗"}')
    print(f'总用电绿电比例:        {ind["green_ratio"]:.2%}  (要求>30%) {"✓" if ind["green_ratio_pass"] else "✗"}')
    print(f'上网电量比例:          {ind["curtail_ratio"]:.2%}  (要求<20%) {"✓" if ind["curtail_pass"] else "✗"}')
    print()
    print(f'净电费:                {results["net_elec_cost"]:.2f} 元')
    print(f'发电成本:              {results["gen_cost"]:.2f} 元')
    print(f'吨氨成本:              {results["cost_per_ton"]:.2f} 元/吨')
    print('=' * 60)

if __name__ == '__main__':
    cfg = Config()
    results = run_q1()
    print_q1_results(results, cfg)
    plot_q1_results(results, cfg)
    print('Q1 figures saved.')
