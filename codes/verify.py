import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
from q1_simulation import run_q1
from q2_scheduling import analyze_production_level
from q3_continuous import analyze_continuous_production
from q4_offgrid import offgrid_without_storage, calc_offgrid_cost

cfg = Config()

print("=" * 70)
print("【验证脚本】逐项检查各问题结果的正确性")
print("=" * 70)

print("\n--- Q1: 功率平衡与指标验证 ---")
P_wind = cfg.P_wind_typ
P_pv = cfg.P_pv_typ
P_conv = cfg.P_conv
P_prod = 20.75
P_re = P_wind + P_pv
net = P_re - P_conv - P_prod

E_re = np.sum(P_re)
E_load = np.sum(P_conv)
E_prod = P_prod * 24
E_total = E_load + E_prod
E_buy = np.sum(np.maximum(0, -net))
E_sell = np.sum(np.maximum(0, net))

balance = E_re + E_buy - E_total - E_sell
print(f"  总可再生={E_re:.2f} MWh")
print(f"  总用电={E_total:.2f} MWh (负荷={E_load:.2f} + 生产={E_prod:.2f})")
print(f"  网购={E_buy:.2f} MWh, 上网={E_sell:.2f} MWh")
print(f"  平衡检查: E_re+E_buy-E_total-E_sell = {balance:.4f} (应≈0)")

if abs(balance) > 0.01:
    print("  ❌ 功率平衡不成立!")
else:
    print("  ✓ 功率平衡成立")

q1 = run_q1()
for key in ["E_re", "E_total", "E_sell", "E_buy"]:
    diff = abs(q1[key] - eval(key))
    mark = "✓" if diff < 0.1 else "❌"
    print(f"  {mark} {key} = {q1[key]:.2f} (期望≈{eval(key):.2f})")

sc = (E_total - E_sell - E_buy) / E_re
gr = (E_re - E_sell) / E_total
cur = E_sell / E_re
ind = q1["indicators"]
for name, val, exp in [("自用比例", ind["self_consume_ratio"], sc),
                         ("绿电比例", ind["green_ratio"], gr),
                         ("上网比例", ind["curtail_ratio"], cur)]:
    mark = "✓" if abs(val - exp) < 0.005 else "❌"
    print(f"  {mark} {name}={val:.2%} (期望≈{exp:.2%})")

print("\n--- Q2: 离散调度优化验证 ---")
prod72 = cfg.get_production_power(72)
print(f"  72t/d产能: 总功率={prod72['total']:.1f}MW, 产率={prod72['nh3_rate_th']:.2f}t/h")
print(f"  24h理论产氨={prod72['nh3_rate_th']*24:.1f}t")

scen = {"P_wind": P_wind, "P_pv": P_pv}
results = {}
for cap in [72, 63, 54, 45, 36]:
    r = analyze_production_level(cfg, scen, cap)
    results[cap] = r
    expected_hours = int(cap / 72 * 24)
    mark_h = "✓" if r["hours_run"] == expected_hours else "❌"
    mark_p = "✓" if abs(r["nh3_production"] - cap) < 0.1 else "❌"
    print(f"  {mark_h} {cap}t/d: 运行时={r['hours_run']}h (期望={expected_hours})")
    print(f"  {mark_p}           实产={r['nh3_production']:.1f}t (期望={cap})")

print("\n--- Q3: 连续调节验证 ---")
for cap in [72, 63, 54, 45, 36]:
    r3 = analyze_continuous_production(cfg, scen, cap)
    mark = "✓" if abs(r3["nh3_production"] - cap) < 1.0 else "❌"
    print(f"  {mark} Q3 {cap}t/d: 实产={r3['nh3_production']:.1f}t, 成本={r3['cost_per_ton']:.0f}元")
    ind3 = r3["indicators"]
    print(f"      自用={ind3['self_consume_ratio']:.1%} 绿电={ind3['green_ratio']:.1%} 上网={ind3['curtail_ratio']:.1%}")

print("\n--- Q4: 离网运行验证 ---")
P_prod_max = prod72["total"]
P_prod_min = P_prod_max * 0.1
p_prod, P_curtail, nh3_prod, total_curt, re_util = offgrid_without_storage(
    P_wind, P_pv, P_conv, cfg, P_prod_max, P_prod_min)

below_min = np.sum((p_prod > 0) & (p_prod < P_prod_min - 0.01))
print(f"  产量={nh3_prod:.1f}t, 弃电={total_curt:.1f}MWh")
print(f"  可再生利用率={re_util:.1%}")
below_mark = "✓" if below_min == 0 else f"❌ (有{below_min}个)"
print(f"  功率低于10%下限的时段: {below_mark}")

total_cost, cpt, gc, oc, dc = calc_offgrid_cost(nh3_prod, cfg)
print(f"  吨氨成本={cpt:.0f}元 (发电={gc:.0f} + 运维={oc:.0f} + 折旧={dc:.0f})")

print("\n" + "=" * 70)
print("【验证结论】")
print("=" * 70)
all_pass = True

if abs(balance) > 0.01:
    print("❌ Q1: 功率平衡不成立")
    all_pass = False
for key in ["E_re", "E_total"]:
    if abs(q1[key] - eval(key)) > 0.1:
        print(f"❌ Q1: {key}不一致")
        all_pass = False

print("✓ Q1: 功率平衡和指标计算通过" if all_pass else "")

for cap in [72, 63, 54, 45, 36]:
    r = results[cap]
    if r["hours_run"] != int(cap / 72 * 24) or abs(r["nh3_production"] - cap) > 0.1:
        print(f"❌ Q2: {cap}t/d产量或运行时错误")
        all_pass = False

print("✓ Q2: 所有产量水平正确" if all_pass else "")

for cap in [72, 63, 54, 45, 36]:
    r3 = analyze_continuous_production(cfg, scen, cap)
    if abs(r3["nh3_production"] - cap) > 1.0:
        print(f"❌ Q3: {cap}t/d产量偏差{r3['nh3_production']-cap:.1f}t")
        all_pass = False

print("✓ Q3: 所有产量水平正确" if all_pass else "")

if below_min > 0:
    print(f"❌ Q4: 有{below_min}个时段功率低于下限")
    all_pass = False

print("✓ Q4: 功率约束满足" if all_pass else "")

if all_pass:
    print("\n🎉 所有验证通过！结果正确。")
else:
    print(f"\n⚠️  发现问题，需要修正。")
