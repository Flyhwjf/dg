import numpy as np
from config import Config

def power_balance(P_wind, P_pv, P_conv, P_prod):
    P_re = P_wind + P_pv
    net = P_re - P_conv - P_prod
    P_buy = np.maximum(0, -net)
    P_sell = np.maximum(0, net)
    return P_buy, P_sell, P_re

def calc_daily_energy(P_wind, P_pv, P_conv, P_prod, P_buy, P_sell):
    E_re = np.sum(P_wind + P_pv)
    E_total = np.sum(P_conv + P_prod)
    E_sell = np.sum(P_sell)
    E_buy = np.sum(P_buy)
    E_self = E_re - E_sell
    return E_re, E_total, E_sell, E_buy, E_self

def calc_green_indicators(E_re, E_total, E_sell, E_buy, cfg):
    self_consume_ratio = (E_total - E_sell - E_buy) / E_re if E_re > 0 else 0
    green_ratio = (E_re - E_sell) / E_total if E_total > 0 else 0
    curtail_ratio = E_sell / E_re if E_re > 0 else 0
    return {
        'self_consume_ratio': self_consume_ratio,
        'green_ratio': green_ratio,
        'curtail_ratio': curtail_ratio,
        'self_consume_pass': self_consume_ratio >= cfg.REQUIRE_SELF_CONSUME,
        'green_ratio_pass': green_ratio >= cfg.REQUIRE_GREEN_RATIO,
        'curtail_pass': curtail_ratio <= cfg.REQUIRE_CURTAIL_RATIO,
        'all_pass': (self_consume_ratio >= cfg.REQUIRE_SELF_CONSUME and
                     green_ratio >= cfg.REQUIRE_GREEN_RATIO and
                     curtail_ratio <= cfg.REQUIRE_CURTAIL_RATIO)
    }

def calc_electricity_cost(P_buy, P_sell, price_buy, price_sell):
    cost_purchase = np.sum(P_buy * price_buy)
    revenue_sales = np.sum(P_sell * price_sell)
    return cost_purchase - revenue_sales

def calc_ammonia_cost(electricity_net_cost, nh3_production_t, cfg, capacity_tpd):
    om_cost = calc_om_cost(nh3_production_t, cfg, capacity_tpd)
    total_cost = electricity_net_cost + om_cost
    cost_per_ton = total_cost / nh3_production_t if nh3_production_t > 0 else 0
    return total_cost, cost_per_ton

def calc_generation_cost(cfg):
    P_wind_avg = np.mean(cfg.P_wind_typ)
    P_pv_avg = np.mean(cfg.P_pv_typ)
    daily_wind_energy = np.sum(cfg.P_wind_typ)
    daily_pv_energy = np.sum(cfg.P_pv_typ)
    return daily_wind_energy * cfg.wind_cost + daily_pv_energy * cfg.pv_cost

def calc_om_cost(nh3_production_t, cfg, capacity_tpd):
    scale = capacity_tpd / 36.0
    hours_prod = nh3_production_t / (cfg.nh3_rate_th * scale)
    alkel_energy = cfg.alkel_power_MW * scale * hours_prod
    pemel_energy = cfg.pemel_power_MW * scale * hours_prod
    nh3_energy = cfg.nh3_power_MW * scale * hours_prod
    return alkel_energy * cfg.alkel_om + pemel_energy * cfg.pemel_om + nh3_energy * cfg.nh3_om

def calc_depreciation_cost(cfg, capacity_tpd):
    scale = capacity_tpd / 36.0
    alkel_cap = cfg.alkel_power_MW * scale * 1000 * 0.15
    pemel_cap = cfg.pemel_power_MW * scale * 1000 * 0.15
    h2_rate = (cfg.alkel_h2_kgh + cfg.pemel_h2_kgh) * scale
    nh3_cap = h2_rate * cfg.nh3_inv / 10000
    storage_cap = 0
    total_inv = alkel_cap + pemel_cap + nh3_cap + storage_cap
    daily_dep = total_inv / (cfg.equip_life * 365)
    return daily_dep

def calc_depreciation_annual(cfg, capacity_tpd):
    scale = capacity_tpd / 36.0
    alkel_power_kw = cfg.alkel_power_MW * scale * 1000
    pemel_power_kw = cfg.pemel_power_MW * scale * 1000
    h2_rate_kgh = (cfg.alkel_h2_kgh + cfg.pemel_h2_kgh) * scale
    
    alkel_inv = alkel_power_kw * 0.15
    pemel_inv = pemel_power_kw * 0.15
    nh3_inv = h2_rate_kgh * cfg.nh3_inv
    
    total_inv = alkel_inv + pemel_inv + nh3_inv
    annual_dep = total_inv / cfg.equip_life
    return annual_dep

def classify_scenario_indicators(indicators):
    passed = sum([indicators['self_consume_pass'],
                  indicators['green_ratio_pass'],
                  indicators['curtail_pass']])
    if passed == 3:
        return 'all_pass'
    elif passed >= 1:
        return 'partial_pass'
    else:
        return 'no_pass'

def generate_24_scenarios(cfg):
    wind_scens = cfg.wind_scenarios
    pv_scens = cfg.pv_scenarios
    scenarios = []
    for wi in range(wind_scens.shape[1]):
        for si in range(pv_scens.shape[1]):
            p_wind = cfg.P_wind_MW * wind_scens[:, wi]
            p_pv = cfg.P_pv_MW * pv_scens[:, si]
            scenarios.append({
                'id': wi * pv_scens.shape[1] + si + 1,
                'wind_idx': wi + 1,
                'pv_idx': si + 1,
                'P_wind': p_wind,
                'P_pv': p_pv,
                'P_re': p_wind + p_pv,
                'wind_label': f'风电{wi+1}',
                'pv_label': f'光伏{si+1}',
                'label': f'S{wi * pv_scens.shape[1] + si + 1}(风{wi+1}光{si+1})'
            })
    return scenarios

def get_production_mode_name(mode):
    names = {0: '全不满足', 1: '部分满足', 2: '全满足'}
    return names.get(mode, '未知')

def running_hours_for_level(capacity_tpd, max_capacity_tpd=72):
    return int(round(capacity_tpd / max_capacity_tpd * 24))

def level_to_capacity(level_idx, max_cap=72, step=9):
    return max_cap - level_idx * step
