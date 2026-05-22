import os, csv, numpy as np

TBL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables')
os.makedirs(TBL_DIR, exist_ok=True)

def _w(filename, rows):
    path = os.path.join(TBL_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)
    print(f'  CSV: {filename}')
    return path

def save_q1(q1, cfg):
    rows = [
        ['时段', '风电功率MW', '光伏功率MW', '常规负荷MW', '制氢氨功率MW',
         '网购功率MW', '售电功率MW', '净负荷MW'],
    ]
    P_re = q1['P_wind'] + q1['P_pv']
    net = P_re - q1['P_conv'] - q1['P_prod']
    for t in range(24):
        rows.append([
            f'{t}:00', f'{q1["P_wind"][t]:.2f}', f'{q1["P_pv"][t]:.2f}',
            f'{q1["P_conv"][t]:.2f}', f'{q1["P_prod"][t]:.2f}',
            f'{q1["P_buy"][t]:.2f}', f'{q1["P_sell"][t]:.2f}', f'{net[t]:.2f}'
        ])
    _w('q1_power_balance.csv', rows)

    ind = q1['indicators']
    rows2 = [
        ['指标', '数值', '要求', '达标'],
        ['新能源发电量MWh', f'{q1["E_re"]:.2f}', '--', '--'],
        ['总用电量MWh', f'{q1["E_total"]:.2f}', '--', '--'],
        ['上网电量MWh', f'{q1["E_sell"]:.2f}', '--', '--'],
        ['网购电量MWh', f'{q1["E_buy"]:.2f}', '--', '--'],
        ['自发自用比例', f'{ind["self_consume_ratio"]:.2%}', '>=60%',
         '达标' if ind['self_consume_pass'] else '不达标'],
        ['总用电绿电比例', f'{ind["green_ratio"]:.2%}', '>=30%',
         '达标' if ind['green_ratio_pass'] else '不达标'],
        ['上网电量比例', f'{ind["curtail_ratio"]:.2%}', '<=20%',
         '达标' if ind['curtail_pass'] else '不达标'],
        ['吨氨成本元吨', f'{q1["cost_per_ton"]:.2f}', '--', '--'],
    ]
    _w('q1_indicators.csv', rows2)

def save_q2(q2, cfg):
    levels = q2['production_levels']
    typ = q2['typical_results']
    rows = [['日产量t_d', '运行小时h', '吨氨成本元_t', '自用比例',
             '绿电比例', '上网比例', '全达标']]
    for l in levels:
        r = typ[l]
        ind = r['indicators']
        rows.append([
            str(l), str(r['hours_run']), f'{r["cost_per_ton"]:.2f}',
            f'{ind["self_consume_ratio"]:.2%}', f'{ind["green_ratio"]:.2%}',
            f'{ind["curtail_ratio"]:.2%}', '是' if ind['all_pass'] else '否'
        ])
    _w('q2_typical.csv', rows)

    scens = q2['scenarios']
    all_r = q2['all_results']
    rows2 = [['场景'] + [f'{l}t_d' for l in levels]]
    for i, s in enumerate(scens):
        row = [s['label']]
        for l in levels:
            if i < len(all_r.get(l, [])):
                row.append(f'{all_r[l][i]["cost_per_ton"]:.0f}')
            else:
                row.append('')
        rows2.append(row)
    _w('q2_scenario_costs.csv', rows2)

    rows3 = [['日产量t_d', '全满足', '部分满足', '全不满足']]
    for l in levels:
        c = q2['compliance_counts'][l]
        rows3.append([str(l), str(c['all_pass']), str(c['partial_pass']), str(c['no_pass'])])
    _w('q2_compliance.csv', rows3)

def save_q3(q3, cfg):
    levels = q3['production_levels']
    typ = q3['q3_typical']
    rows = [['日产量t_d', '实产t', '吨氨成本元_t', '自用比例', '绿电比例', '上网比例']]
    for l in levels:
        r = typ[l]
        ind = r['indicators']
        rows.append([
            str(l), f'{r["nh3_production"]:.1f}', f'{r["cost_per_ton"]:.2f}',
            f'{ind["self_consume_ratio"]:.2%}', f'{ind["green_ratio"]:.2%}',
            f'{ind["curtail_ratio"]:.2%}'
        ])
    _w('q3_typical.csv', rows)

    rows2 = [['日产量t_d', '全满足', '部分满足', '全不满足']]
    for l in levels:
        c = q3['compliance_counts'][l]
        rows2.append([str(l), str(c['all_pass']), str(c['partial_pass']), str(c['no_pass'])])
    _w('q3_compliance.csv', rows2)

def save_q4(q4, cfg):
    from utils import generate_24_scenarios
    scens = q4['scenarios']
    q4_1 = q4['q4_1_results']
    rows = [['场景', '离网产量t', '弃电MWh', '可再生利用率', '吨氨成本元_t']]
    for i, r in enumerate(q4_1):
        rows.append([
            scens[i]['label'], f'{r["nh3_produced"]:.1f}',
            f'{r["total_curtail"]:.1f}', f'{r["re_util"]:.1%}',
            f'{r["cost_per_ton"]:.0f}'
        ])
    _w('q4_1_offgrid.csv', rows)

    comp = q4['comparison']
    rows2 = [
        ['模式', '吨氨成本元_t', '日产量t', '年产量t', '产能利用率'],
        ['离网无储能', f'{comp["offgrid"]["吨氨成本"]:.0f}',
         f'{comp["offgrid"]["年产量"]/360:.1f}',
         f'{comp["offgrid"]["年产量"]:.0f}',
         f'{comp["offgrid"]["年产量"]/72/360:.1%}'],
        ['联网同等产量', f'{comp["ongrid"]["吨氨成本"]:.0f}',
         f'{comp["ongrid"]["年产量"]/360:.1f}',
         f'{comp["ongrid"]["年产量"]:.0f}',
         f'{comp["ongrid"]["年产量"]/72/360:.1%}'],
    ]
    _w('q4_3_comparison.csv', rows2)

def save_all(q1=None, q2=None, q3=None, q4=None, cfg=None):
    if q1 is not None:
        save_q1(q1, cfg)
    if q2 is not None:
        save_q2(q2, cfg)
    if q3 is not None:
        save_q3(q3, cfg)
    if q4 is not None:
        save_q4(q4, cfg)
