import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
from config import Config, TIME_LABELS, FIG_DIR

try:
    matplotlib.rcParams['font.sans-serif'] = ['SimSun', 'STSong', 'FangSong', 'SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False
except:
    pass

COLORS = {
    'wind': '#2E86AB',
    'solar': '#F18F01',
    'load': '#C73E1D',
    'buy': '#A23B72',
    'sell': '#3B8C5E',
    'alkel': '#4A6FA5',
    'pemel': '#E8A838',
    'nh3': '#BF4E30',
    'grid': '#7A7A7A',
    'storage': '#4CAF50',
    'self_use': '#2E86AB',
    'curtail': '#E74C3C',
    'all_pass': '#27AE60',
    'partial_pass': '#F39C12',
    'no_pass': '#E74C3C',
}

COLOR_LIST = ['#2E86AB', '#F18F01', '#C73E1D', '#A23B72', '#3B8C5E',
              '#4A6FA5', '#E8A838', '#BF4E30', '#7A7A7A', '#4CAF50']

def setup_ax(ax, xlabel='', ylabel='', title='', xlim=None, ylim=None,
             grid=True, legend=True):
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if grid:
        ax.grid(True, alpha=0.3, linestyle='--')
    if legend:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=10, framealpha=0.9)
    ax.tick_params(labelsize=10)

def save_fig(fig, name, subdir='', dpi=300):
    d = os.path.join(FIG_DIR, subdir) if subdir else FIG_DIR
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name)
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path

def plot_power_balance(hours, P_wind, P_pv, P_conv, P_buy, P_sell, P_prod,
                       title='园区典型日功率平衡曲线', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax = axes[0, 0]
    ax.bar(hours, P_wind, label='风电', color=COLORS['wind'], alpha=0.85, width=0.6)
    ax.bar(hours, P_pv, bottom=P_wind, label='光伏', color=COLORS['solar'], alpha=0.85, width=0.6)
    ax.plot(hours, P_conv + P_prod, 'o-', label='总负荷(常规+生产)', color=COLORS['load'],
            linewidth=2, markersize=4)
    setup_ax(ax, '时刻/h', '功率/MW', '风光出力与负荷', grid=True)

    ax = axes[0, 1]
    ax.bar(hours, P_buy, label='网购电量', color=COLORS['buy'], alpha=0.85, width=0.6)
    ax.bar(hours, -P_sell, label='售电(上网)', color=COLORS['sell'], alpha=0.85, width=0.6)
    ax.axhline(y=0, color='black', linewidth=0.5)
    setup_ax(ax, '时刻/h', '功率/MW', '购电与售电', grid=True)

    ax = axes[1, 0]
    net = P_wind + P_pv - P_conv - P_prod
    colors_net = [COLORS['sell'] if v >= 0 else COLORS['buy'] for v in net]
    ax.bar(hours, net, color=colors_net, alpha=0.85, width=0.6, edgecolor='white', linewidth=0.3)
    ax.axhline(y=0, color='black', linewidth=0.8)
    setup_ax(ax, '时刻/h', '功率/MW', '净负荷(正=余电上网，负=购电)', grid=True)

    ax = axes[1, 1]
    ax.stackplot(hours,
                 [P_wind, P_pv, P_buy],
                 labels=['风电', '光伏', '网购'],
                 colors=[COLORS['wind'], COLORS['solar'], COLORS['buy']],
                 alpha=0.8)
    ax.stackplot(hours,
                 [P_conv, P_prod, P_sell],
                 labels=['常规负荷', '制氢氨负荷', '售电'],
                 colors=[COLORS['load'], COLORS['alkel'], COLORS['sell']],
                 alpha=0.6)
    setup_ax(ax, '时刻/h', '功率/MW', '能量平衡堆叠图', grid=True)

    fig.suptitle(title, fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_green_indicators_radar(indicators, requirements, title='绿电指标达标分析',
                                save_path=None):
    labels = list(indicators.keys())
    values = list(indicators.values())
    reqs = [requirements.get(k, 0) for k in labels]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values += values[:1]
    reqs += reqs[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.fill(angles, values, alpha=0.25, color=COLORS['wind'])
    ax.plot(angles, values, 'o-', linewidth=2, color=COLORS['wind'], label='实际值')
    ax.fill(angles, reqs, alpha=0.15, color=COLORS['load'])
    ax.plot(angles, reqs, 's--', linewidth=2, color=COLORS['load'], label='要求值')

    for i, (a, v, r) in enumerate(zip(angles[:-1], values[:-1], reqs[:-1])):
        ax.annotate(f'{v:.1%}', xy=(a, v), fontsize=9,
                    ha='center', va='bottom' if v >= r else 'top',
                    color=COLORS['all_pass'] if v >= r else COLORS['no_pass'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 1.1 * max(max(values), max(reqs)))
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_gantt_chart(cfg, run_schedule, capacity, title=None, save_path=None):
    hours = np.arange(24)
    n_levels = len(run_schedule)

    fig, axes = plt.subplots(n_levels, 1, figsize=(14, 2.5 * n_levels + 1), sharex=True)
    if n_levels == 1:
        axes = [axes]

    price_colors = {0.3424: '#E8F5E9', 0.6074: '#FFF8E1', 0.8024: '#FFEBEE'}

    for idx, (cap, sched) in enumerate(zip(capacity, run_schedule)):
        ax = axes[idx]
        for h in hours:
            p = cfg.price_buy[int(h)]
            if p == 0.3424:
                c = '#E8F5E9'
            elif p == 0.6074:
                c = '#FFF8E1'
            else:
                c = '#FFEBEE'
            ax.axvspan(h - 0.5, h + 0.5, facecolor=c, alpha=0.6)

        for h, running in enumerate(sched):
            if running:
                ax.barh(0, 1, left=h - 0.45, height=0.5, color=COLORS['alkel'],
                        alpha=0.85, edgecolor='white', linewidth=0.5)

        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(-0.6, 0.6)
        ax.set_yticks([])
        ax.set_ylabel(f'{cap} t/d', fontsize=11, fontweight='bold')
        ax.grid(axis='x', alpha=0.3, linestyle='--')

    axes[0].set_title(title or '各产量最优生产时段安排', fontsize=14, fontweight='bold')
    axes[-1].set_xlabel('时刻/h', fontsize=12)
    axes[-1].set_xticks(hours)
    axes[-1].set_xticklabels([f'{int(h)}' for h in hours], fontsize=9, rotation=45)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#E8F5E9', label='谷时段(0.3424元)'),
        Patch(facecolor='#FFF8E1', label='平时段(0.6074元)'),
        Patch(facecolor='#FFEBEE', label='峰时段(0.8024元)'),
        Patch(facecolor=COLORS['alkel'], label='生产运行'),
    ]
    axes[0].legend(handles=legend_elements, loc='upper right', fontsize=9,
                   ncol=4, framealpha=0.9)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_cost_vs_production(production_levels, results, title='指标随产量变化',
                            save_path=None):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    ax = axes[0]
    costs = [r['cost_per_ton'] for r in results]
    ax.plot(production_levels, costs, 'o-', color=COLORS['load'], linewidth=2.5,
            markersize=8, markerfacecolor='white', markeredgewidth=2)
    min_idx = np.argmin(costs)
    ax.plot(production_levels[min_idx], costs[min_idx], '*', color='gold',
            markersize=18, markeredgecolor='black', markeredgewidth=1,
            label=f'最低: {costs[min_idx]:.0f}元/吨')
    for i, (x, y) in enumerate(zip(production_levels, costs)):
        ax.annotate(f'{y:.0f}', (x, y), textcoords='offset points',
                    xytext=(0, 12), ha='center', fontsize=9)
    setup_ax(ax, '日产量/(t/d)', '吨氨成本/(元/吨)', '吨氨成本')
    ax.legend(fontsize=10)

    ax = axes[1]
    for key, color, label, req_val in [
        ('self_consume_ratio', '#2E86AB', '自发自用比例', 0.6),
        ('green_ratio', '#F18F01', '绿电比例', 0.3),
        ('curtail_ratio', '#C73E1D', '上网比例', 0.2),
    ]:
        vals = [r['indicators'][key] for r in results]
        ax.plot(production_levels, vals, 'o-', color=color, linewidth=2,
                markersize=6, label=label)
        ax.axhline(y=req_val, color=color, linestyle='--', linewidth=1.2, alpha=0.7)

    setup_ax(ax, '日产量/(t/d)', '比例', '绿电直连指标')

    ax = axes[2]
    util_rates = [r['utilization_rate'] for r in results]
    ax.bar(production_levels, util_rates, width=4, color=COLORS['alkel'],
           alpha=0.8, edgecolor='white')
    for x, y in zip(production_levels, util_rates):
        ax.annotate(f'{y:.1%}', (x, y), textcoords='offset points',
                    xytext=(0, 8), ha='center', fontsize=9)
    setup_ax(ax, '日产量/(t/d)', '设备利用率', '制氢氨设备利用率')

    fig.suptitle(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_24_scenarios_heatmap(scenario_ids, production_levels, cost_matrix,
                              title='24场景×5产量吨氨成本热力图', save_path=None):
    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(cost_matrix, aspect='auto', cmap='YlOrRd')

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('吨氨成本(元/吨)', fontsize=11)

    ax.set_xticks(np.arange(len(production_levels)))
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=10)
    ax.set_yticks(np.arange(len(scenario_ids)))
    ax.set_yticklabels(scenario_ids, fontsize=8)

    for i in range(cost_matrix.shape[0]):
        for j in range(cost_matrix.shape[1]):
            val = cost_matrix[i, j]
            ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                    fontsize=7, color='black' if val < np.nanmax(cost_matrix) * 0.6 else 'white')

    ax.set_xlabel('日产量', fontsize=12)
    ax.set_ylabel('风光场景', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_scenario_compliance(counts_by_level, production_levels,
                             title='各产量绿电指标达标统计', save_path=None):
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(production_levels))
    width = 0.5

    bottom = np.zeros(len(production_levels))
    categories = [
        ('全满足', 'all_pass', COLORS['all_pass']),
        ('部分满足', 'partial_pass', COLORS['partial_pass']),
        ('全不满足', 'no_pass', COLORS['no_pass']),
    ]

    for label, key, color in categories:
        vals = [counts_by_level[l][key] for l in production_levels]
        ax.bar(x, vals, width, bottom=bottom, label=label, color=color,
               alpha=0.85, edgecolor='white')
        for i, v in enumerate(vals):
            if v > 0:
                ax.text(i, bottom[i] + v / 2, str(v), ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white')
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=11)
    ax.set_xlabel('日产量', fontsize=12)
    ax.set_ylabel('场景数量', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper right')
    ax.set_ylim(0, 28)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_annual_cost_distribution(costs_by_level, production_levels,
                                  title='全年吨氨成本分布', save_path=None):
    n_levels = len(production_levels)
    fig, axes = plt.subplots(n_levels, 1, figsize=(12, 3.5 * n_levels), sharex=True)
    if n_levels == 1:
        axes = [axes]

    for idx, (ax, level) in enumerate(zip(axes, production_levels)):
        costs = costs_by_level[level]
        mean_val = np.mean(costs)
        std_val = np.std(costs)

        ax.hist(costs, bins=12, density=True, alpha=0.6,
                color=COLOR_LIST[idx % len(COLOR_LIST)], edgecolor='white')

        x_smooth = np.linspace(min(costs), max(costs), 200)
        from scipy import stats
        kernel = stats.gaussian_kde(costs)
        ax.plot(x_smooth, kernel(x_smooth), '-', color=COLOR_LIST[idx % len(COLOR_LIST)],
                linewidth=2.5, label=f'概率密度')

        ax.axvline(mean_val, color='#E74C3C', linestyle='--', linewidth=2,
                   label=f'均值={mean_val:.0f}')
        ax.axvline(mean_val - std_val, color='#95A5A6', linestyle=':', linewidth=1.5)
        ax.axvline(mean_val + std_val, color='#95A5A6', linestyle=':', linewidth=1.5)

        ax.set_ylabel('概率密度', fontsize=10)
        ax.set_title(f'日产量 {level} t/d', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    axes[-1].set_xlabel('吨氨成本/(元/吨)', fontsize=12)
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_comparison_q2_q3(production_levels, q2_costs, q3_costs, q2_indicators, q3_indicators,
                          title='Q2 vs Q3 对比分析', save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    ax = axes[0]
    x = np.arange(len(production_levels))
    w = 0.35
    ax.bar(x - w / 2, q2_costs, w, label='离散调节(Q2)', color=COLORS['load'], alpha=0.8)
    ax.bar(x + w / 2, q3_costs, w, label='连续调节(Q3)', color=COLORS['wind'], alpha=0.8)

    for i in range(len(production_levels)):
        improvement = (q2_costs[i] - q3_costs[i]) / q2_costs[i] * 100
        ax.annotate(f'{improvement:.1f}%', (x[i], max(q2_costs[i], q3_costs[i])),
                    textcoords='offset points', xytext=(0, 8),
                    ha='center', fontsize=9, fontweight='bold',
                    color=COLORS['all_pass'] if improvement > 0 else COLORS['no_pass'])

    ax.set_xticks(x)
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=11)
    setup_ax(ax, '日产量', '吨氨成本/(元/吨)', '吨氨成本对比')

    ax = axes[1]
    metrics = ['self_consume_ratio', 'green_ratio', 'curtail_ratio']
    labels = ['自发自用比例', '绿电比例', '上网比例']
    x = np.arange(len(metrics))
    w = 0.35
    for idx, level in enumerate(production_levels):
        offset = (idx - 2) * w
        q2_vals = [q2_indicators[level][m] for m in metrics]
        q3_vals = [q3_indicators[level][m] for m in metrics]
        ax.bar(x + offset, q2_vals, w * 0.4, alpha=0.6,
               color=COLOR_LIST[idx], label=f'Q2 {level}t/d')
        ax.bar(x + offset + w * 0.4, q3_vals, w * 0.4, alpha=0.9,
               color=COLOR_LIST[idx], label=f'Q3 {level}t/d', hatch='//')

    ax.axhline(y=0.6, color='gray', linestyle='--', linewidth=1)
    ax.axhline(y=0.3, color='gray', linestyle='--', linewidth=1)
    ax.axhline(y=0.2, color='gray', linestyle='--', linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    setup_ax(ax, '', '比例', 'Q2 vs Q3 绿电指标')
    ax.legend(fontsize=8, ncol=2)

    fig.suptitle(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_sankey_diagram(values, labels, title='能量流向桑基图', save_path=None):
    try:
        import matplotlib.sankey as sankey
        fig, ax = plt.subplots(figsize=(10, 6))
        sankey.Sankey(ax=ax, unit='MWh', format='%.1f',
                      scale=0.01, offset=0.2, head_angle=120).add(
            flows=values,
            labels=labels,
            orientations=[0, 0, 1, -1, 0, 0],
            pathlengths=[0.5]*len(values),
            colors=[COLORS[c] for c in ['wind', 'solar', 'load', 'alkel', 'sell', 'buy']]
        ).finish()
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
        return fig
    except:
        fig, ax = plt.subplots(figsize=(10, 6))
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=[COLORS[c] for c in ['wind', 'solar', 'load', 'alkel', 'sell', 'buy']],
            startangle=90, explode=[0.02]*len(values)
        )
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
        return fig

def plot_pareto_storage(storage_caps, costs, curtail_rates,
                        title='储能容量优化Pareto曲线', save_path=None):
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color1 = COLORS['wind']
    ax1.plot(storage_caps, costs, 'o-', color=color1, linewidth=2.5,
             markersize=8, markerfacecolor='white', markeredgewidth=2,
             label='吨氨成本')
    ax1.set_xlabel('储能容量/MWh', fontsize=12)
    ax1.set_ylabel('吨氨成本/(元/吨)', fontsize=12, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = COLORS['curtail']
    ax2.plot(storage_caps, curtail_rates, 's--', color=color2, linewidth=2,
             markersize=8, markerfacecolor='white', markeredgewidth=2,
             label='弃电率')
    ax2.set_ylabel('弃电率', fontsize=12, color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

    knee_idx = np.argmin(np.diff(costs) / np.diff(storage_caps))
    ax1.axvline(x=storage_caps[knee_idx], color='gray', linestyle=':',
                linewidth=1.5, alpha=0.7)
    ax1.annotate(f'膝点: {storage_caps[knee_idx]:.1f} MWh',
                 xy=(storage_caps[knee_idx], costs[knee_idx]),
                 xytext=(storage_caps[knee_idx] * 1.3, costs[knee_idx] * 1.1),
                 fontsize=11, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_soc_discharge(soc_data, ch_data, dis_data, hours, title='储能SOC与充放电功率',
                       save_path=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for key in soc_data:
        ax1.plot(hours, soc_data[key], '-', linewidth=2, label=key)
    ax1.set_ylabel('SOC/%', fontsize=12)
    ax1.set_title('荷电状态变化', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 105)

    ax2.bar(hours, ch_data, label='充电', color=COLORS['storage'], alpha=0.7, width=0.6)
    ax2.bar(hours, -dis_data, label='放电', color=COLORS['sell'], alpha=0.7, width=0.6)
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_xlabel('时刻/h', fontsize=12)
    ax2.set_ylabel('功率/MW', fontsize=12)
    ax2.set_title('充放电功率', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_offgrid_comparison(scenarios, with_storage_data, without_storage_data,
                            title='离网运行有无储能对比', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    labels = [s['label'] for s in scenarios]
    x = np.arange(len(labels))

    ax = axes[0, 0]
    ax.bar(x - 0.2, without_storage_data['curtail_rates'], 0.35,
           label='无储能', color=COLORS['load'], alpha=0.7)
    ax.bar(x + 0.2, with_storage_data['curtail_rates'], 0.35,
           label='有储能', color=COLORS['storage'], alpha=0.7)
    setup_ax(ax, '场景', '弃电率', '弃电率对比')
    ax.legend(fontsize=10)

    ax = axes[0, 1]
    ax.bar(x - 0.2, without_storage_data['productions'], 0.35,
           label='无储能', color=COLORS['load'], alpha=0.7)
    ax.bar(x + 0.2, with_storage_data['productions'], 0.35,
           label='有储能', color=COLORS['storage'], alpha=0.7)
    setup_ax(ax, '场景', '产量/(t/d)', '日产量对比')
    ax.legend(fontsize=10)

    ax = axes[1, 0]
    ax.bar(x - 0.2, without_storage_data['util_rates'], 0.35,
           label='无储能', color=COLORS['load'], alpha=0.7)
    ax.bar(x + 0.2, with_storage_data['util_rates'], 0.35,
           label='有储能', color=COLORS['storage'], alpha=0.7)
    setup_ax(ax, '场景', '产能利用率', '产能利用率对比')
    ax.legend(fontsize=10)

    ax = axes[1, 1]
    ax.bar(x - 0.2, without_storage_data['re_util_rates'], 0.35,
           label='无储能', color=COLORS['load'], alpha=0.7)
    ax.bar(x + 0.2, with_storage_data['re_util_rates'], 0.35,
           label='有储能', color=COLORS['storage'], alpha=0.7)
    setup_ax(ax, '场景', '可再生利用率', '可再生能源利用率对比')
    ax.legend(fontsize=10)

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_offgrid_power_balance(hours, P_wind, P_pv, P_conv, P_prod, P_curtail,
                               title='离网运行功率平衡', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax = axes[0, 0]
    ax.plot(hours, P_wind, 'o-', label='风电', color=COLORS['wind'], linewidth=2)
    ax.plot(hours, P_pv, 's-', label='光伏', color=COLORS['solar'], linewidth=2)
    ax.plot(hours, P_conv + P_prod, '^-', label='总负荷', color=COLORS['load'], linewidth=2)
    setup_ax(ax, '时刻/h', '功率/MW', '可再生出力与负荷')

    ax = axes[0, 1]
    ax.bar(hours, P_curtail, color=COLORS['curtail'], alpha=0.8, width=0.6)
    setup_ax(ax, '时刻/h', '弃电功率/MW', '弃电量')

    ax = axes[1, 0]
    ax.fill_between(hours, 0, P_prod, label='制氨功率', color=COLORS['alkel'], alpha=0.7)
    ax.plot(hours, P_wind + P_pv - P_conv, '--', color='gray', label='可用功率(可再生-负荷)')
    setup_ax(ax, '时刻/h', '功率/MW', '制氨功率跟随可再生出力')

    ax = axes[1, 1]
    total_avail = np.sum(P_wind + P_pv - P_conv)
    total_used = np.sum(P_prod)
    total_curtailed = np.sum(P_curtail)
    ax.pie([max(0, total_used), max(0, total_curtailed), max(0, -total_avail)],
           labels=['自用', '弃电', '缺电'],
           autopct='%1.1f%%',
           colors=[COLORS['all_pass'], COLORS['curtail'], COLORS['buy']],
           startangle=90)
    ax.set_title('能量分配', fontsize=13, fontweight='bold')

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_production_vs_curtailment(scenario_labels, productions, curtail_rates,
                                    title='各场景产量与弃电分析', save_path=None):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    sort_idx = np.argsort(curtail_rates)[::-1]
    labels_sorted = [scenario_labels[i] for i in sort_idx]
    prods_sorted = [productions[i] for i in sort_idx]
    curtails_sorted = [curtail_rates[i] for i in sort_idx]

    x = np.arange(len(labels_sorted))
    ax1.bar(x, prods_sorted, 0.6, label='日产量', color=COLORS['alkel'], alpha=0.8)
    ax1.set_ylabel('日产量/(t/d)', fontsize=12, color=COLORS['alkel'])

    ax2 = ax1.twinx()
    ax2.plot(x, curtails_sorted, 'o-', color=COLORS['curtail'], linewidth=2.5,
             markersize=8, label='弃电率')
    ax2.axhline(y=0.2, color=COLORS['no_pass'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.set_ylabel('弃电率', fontsize=12, color=COLORS['curtail'])

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_sorted, fontsize=8, rotation=45, ha='right')
    ax1.set_xlabel('场景', fontsize=12)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_net_vs_offgrid_comparison(comparison_data, title='离网与联网模式经济性对比',
                                    save_path=None):
    metrics = ['吨氨成本', '净电费', '年产量', '能自给率']
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(metrics))
    w = 0.35

    ongrid_vals = [comparison_data['ongrid'].get(m, 0) for m in metrics]
    offgrid_vals = [comparison_data['offgrid'].get(m, 0) for m in metrics]

    ax.bar(x - w / 2, ongrid_vals, w, label='联网模式', color=COLORS['wind'], alpha=0.8)
    ax.bar(x + w / 2, offgrid_vals, w, label='离网模式', color=COLORS['storage'], alpha=0.8)

    for i in range(len(metrics)):
        ratio = offgrid_vals[i] / ongrid_vals[i] * 100 if ongrid_vals[i] != 0 else 0
        ax.text(i, max(ongrid_vals[i], offgrid_vals[i]) * 1.05,
                f'{ratio:.0f}%', ha='center', fontsize=10, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=12)
    setup_ax(ax, '', '', '经济性与能源自给对比')
    ax.legend(fontsize=11)

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_policy_analysis(save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    ax = axes[0]
    impacts = ['调峰压力增大', '备用容量需求增加', '电能质量挑战',
               '促进新能源消纳', '降低系统碳排放', '推动储能技术发展']
    directions = [-1, -1, -1, 1, 1, 1]
    magnitudes = [0.85, 0.7, 0.6, 0.9, 0.95, 0.75]
    colors_impact = [COLORS['no_pass'] if d < 0 else COLORS['all_pass'] for d in directions]
    y_pos = np.arange(len(impacts))

    ax.barh(y_pos, [d * m for d, m in zip(directions, magnitudes)],
            color=colors_impact, alpha=0.8, height=0.6)
    for i, (imp, d, m) in enumerate(zip(impacts, directions, magnitudes)):
        label = f'{imp} ({abs(m):.0%})'
        ax.text(0.02 if d > 0 else -0.02, i, label,
                ha='left' if d > 0 else 'right', va='center',
                fontsize=10, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([])
    ax.set_xlim(-1.2, 1.2)
    ax.set_title('绿电园区高渗透率对电网影响', fontsize=13, fontweight='bold')
    ax.text(-1.1, -0.5, '← 不利影响', fontsize=10, color=COLORS['no_pass'], fontweight='bold')
    ax.text(1.05, -0.5, '有利影响 →', fontsize=10, color=COLORS['all_pass'], fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    ax = axes[1]
    policies = ['完善市场机制', '配置储能', '智能调度', '政策激励', '技术研发']
    values = [0.88, 0.82, 0.75, 0.92, 0.78]
    ax.barh(policies, values, color=COLORS['wind'], alpha=0.8, height=0.5)
    for i, v in enumerate(values):
        ax.text(v + 0.02, i, f'{v:.0%}', va='center', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 1.1)
    ax.set_title('政策建议框架', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    fig.suptitle('绿电直连园区发展影响与政策建议', fontsize=15, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_compliance_comparison(production_levels, q2_counts, q3_counts,
                               title='Q2 vs Q3 达标统计对比', save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    for idx, (ax, counts, label) in enumerate(zip(
            axes, [q2_counts, q3_counts], ['离散调节(Q2)', '连续调节(Q3)'])):
        x = np.arange(len(production_levels))
        w = 0.5
        bottom = np.zeros(len(production_levels))
        for key, color in [('all_pass', COLORS['all_pass']),
                            ('partial_pass', COLORS['partial_pass']),
                            ('no_pass', COLORS['no_pass'])]:
            vals = [counts[l][key] for l in production_levels]
            ax.bar(x, vals, w, bottom=bottom, color=color, alpha=0.85,
                   edgecolor='white', label={'all_pass': '全满足',
                                            'partial_pass': '部分满足',
                                            'no_pass': '全不满足'}[key])
            for i, v in enumerate(vals):
                if v > 0:
                    ax.text(i, bottom[i] + v / 2, str(v), ha='center',
                            va='center', fontsize=10, fontweight='bold', color='white')
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=10)
        ax.set_title(label, fontsize=12, fontweight='bold')
        ax.set_xlabel('日产量', fontsize=11)
        if idx == 0:
            ax.set_ylabel('场景数量', fontsize=11)

    axes[0].legend(fontsize=10)
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig

def plot_q3_power_schedule(hours, P_wind, P_pv, P_conv, P_prod_continuous,
                           P_prod_discrete, P_buy, P_sell, title='连续调节功率调度方案',
                           save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax = axes[0, 0]
    ax.fill_between(hours, 0, P_prod_continuous, label='连续调节制氨功率',
                    color=COLORS['alkel'], alpha=0.6)
    ax.plot(hours, P_wind + P_pv - P_conv, '--', color='gray', linewidth=2,
            label='可用功率')
    setup_ax(ax, '时刻/h', '功率/MW', '连续可调功率方案', grid=True)

    ax = axes[0, 1]
    ax.step(hours, P_prod_discrete, where='mid', label='离散(Q2)', color=COLORS['load'],
            linewidth=2.5)
    ax.fill_between(hours, 0, P_prod_continuous, label='连续(Q3)',
                    color=COLORS['wind'], alpha=0.4)
    setup_ax(ax, '时刻/h', '功率/MW', '离散 vs 连续 调度对比', grid=True)

    ax = axes[1, 0]
    ax.bar(hours, P_buy, label='购电', color=COLORS['buy'], alpha=0.8, width=0.6)
    ax.bar(hours, -P_sell, label='售电', color=COLORS['sell'], alpha=0.8, width=0.6)
    ax.axhline(y=0, color='black', linewidth=0.5)
    setup_ax(ax, '时刻/h', '功率/MW', '购电与售电', grid=True)

    ax = axes[1, 1]
    equiv_load = P_conv + P_prod_continuous
    ax.stackplot(hours, [P_wind, P_pv], labels=['风电', '光伏'],
                 colors=[COLORS['wind'], COLORS['solar']], alpha=0.7)
    ax.plot(hours, equiv_load, '-', color=COLORS['load'], linewidth=2, label='等效总负荷')
    setup_ax(ax, '时刻/h', '功率/MW', '可再生发电与等效负荷', grid=True)

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return fig
