import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os
from config import Config, TIME_LABELS, FIG_DIR

try:
    matplotlib.rcParams['font.sans-serif'] = ['SimSun', 'STSong', 'FangSong', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False
except:
    pass

PUB_RCPARAMS = {
    'font.size': 8.5,
    'axes.linewidth': 0.6,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'xtick.major.width': 0.5,
    'xtick.minor.width': 0.3,
    'ytick.major.width': 0.5,
    'ytick.minor.width': 0.3,
    'xtick.major.size': 3,
    'xtick.minor.size': 1.5,
    'ytick.major.size': 3,
    'ytick.minor.size': 1.5,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7.5,
    'legend.frameon': False,
    'legend.handlelength': 1.2,
    'legend.handletextpad': 0.4,
    'figure.dpi': 150,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
}
matplotlib.rcParams.update(PUB_RCPARAMS)

NMI_PASTEL = {
    'teal': '#7A9E9F',
    'coral': '#CE7E7E',
    'sand': '#D4B68A',
    'sage': '#8FAA8F',
    'lavender': '#9B8EB5',
    'sky': '#7FA8C4',
    'peach': '#D4A08A',
    'mint': '#8FBFA0',
}

SEMANTIC = {
    'wind': '#7A9E9F',
    'solar': '#D4B68A',
    'load': '#CE7E7E',
    'buy': '#9B8EB5',
    'sell': '#8FAA8F',
    'alkel': '#7FA8C4',
    'pemel': '#D4A08A',
    'nh3': '#C48080',
    'grid': '#999999',
    'storage': '#8FBFA0',
    'self_use': '#7A9E9F',
    'curtail': '#C48080',
    'all_pass': '#7A9E9F',
    'partial_pass': '#D4B68A',
    'no_pass': '#CE7E7E',
    'improve': '#7FA8C4',
}

COLOR_LIST = ['#7A9E9F', '#D4B68A', '#CE7E7E', '#9B8EB5', '#8FAA8F',
              '#7FA8C4', '#D4A08A', '#C48080', '#999999', '#8FBFA0']

def setup_ax(ax, xlabel='', ylabel='', title='', xlim=None, ylim=None,
             grid=True, legend=True, xrotation=0):
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8.5, labelpad=2)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, labelpad=2)
    if title:
        ax.set_title(title, fontsize=9, fontweight='bold', pad=4)
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if grid:
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.3)
    if legend:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=7.5, handlelength=1.2, handletextpad=0.4,
                     markerfirst=True, borderpad=0.3)
    ax.tick_params(pad=1.5)
    if xrotation:
        for label in ax.get_xticklabels():
            label.set_rotation(xrotation)
            label.set_ha('right')

def save_fig(fig, name, subdir='', dpi=600):
    d = os.path.join(FIG_DIR, subdir) if subdir else FIG_DIR
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, name.replace('.png', '').replace('.svg', '').replace('.pdf', '').replace('.tiff', ''))
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    fig.savefig(f"{base}.svg", bbox_inches='tight')
    fig.savefig(f"{base}.tiff", dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return f"{base}.pdf"

def plot_power_balance(hours, P_wind, P_pv, P_conv, P_buy, P_sell, P_prod,
                       title='园区典型日功率平衡曲线', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8))

    ax = axes[0, 0]
    ax.bar(hours, P_wind, label='风电', color=SEMANTIC['wind'], alpha=0.85, width=0.7, linewidth=0.2)
    ax.bar(hours, P_pv, bottom=P_wind, label='光伏', color=SEMANTIC['solar'], alpha=0.85, width=0.7, linewidth=0.2)
    ax.plot(hours, P_conv + P_prod, 'o-', label='总负荷', color=SEMANTIC['load'],
            linewidth=1, markersize=2.5, markerfacecolor='white', markeredgewidth=0.5)
    setup_ax(ax, '时刻/h', '功率/MW', '风光出力与负荷')

    ax = axes[0, 1]
    ax.bar(hours, P_buy, label='网购电量', color=SEMANTIC['buy'], alpha=0.85, width=0.7, linewidth=0.2)
    ax.bar(hours, -P_sell, label='售电(上网)', color=SEMANTIC['sell'], alpha=0.85, width=0.7, linewidth=0.2)
    ax.axhline(y=0, color='black', linewidth=0.4)
    setup_ax(ax, '时刻/h', '功率/MW', '购电与售电')
    ax.set_ylim(-max(abs(P_sell)) * 1.3, max(P_buy) * 1.3)

    ax = axes[1, 0]
    net = P_wind + P_pv - P_conv - P_prod
    colors_net = [SEMANTIC['sell'] if v >= 0 else SEMANTIC['buy'] for v in net]
    ax.bar(hours, net, color=colors_net, alpha=0.85, width=0.7, linewidth=0.2, edgecolor='white')
    ax.axhline(y=0, color='black', linewidth=0.4)
    setup_ax(ax, '时刻/h', '功率/MW', '净负荷')

    ax = axes[1, 1]
    ax.stackplot(hours,
                 [P_wind, P_pv, P_buy],
                 labels=['风电', '光伏', '网购'],
                 colors=[SEMANTIC['wind'], SEMANTIC['solar'], SEMANTIC['buy']],
                 alpha=0.75, linewidth=0)
    ax.stackplot(hours,
                 [P_conv, P_prod, P_sell],
                 labels=['常规负荷', '制氢氨负荷', '售电'],
                 colors=[SEMANTIC['load'], SEMANTIC['alkel'], SEMANTIC['sell']],
                 alpha=0.55, linewidth=0)
    setup_ax(ax, '时刻/h', '功率/MW', '能量平衡堆叠图')

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.5)
    if save_path:
        save_fig(fig, save_path)
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

    fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
    ax.fill(angles, values, alpha=0.2, color=SEMANTIC['wind'])
    ax.plot(angles, values, 'o-', linewidth=1.2, color=SEMANTIC['wind'], label='实际值', markersize=3)
    ax.fill(angles, reqs, alpha=0.12, color=SEMANTIC['load'])
    ax.plot(angles, reqs, 's--', linewidth=1.2, color=SEMANTIC['load'], label='要求值', markersize=3)

    for i, (a, v, r) in enumerate(zip(angles[:-1], values[:-1], reqs[:-1])):
        ax.annotate(f'{v:.1%}', xy=(a, v), fontsize=7,
                    ha='center', va='bottom' if v >= r else 'top',
                    color='#3A6B6B' if v >= r else '#B06060')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylim(0, 1.15 * max(max(values), max(reqs)))
    # ax.set_title(title, fontsize=7, fontweight='bold', pad=10)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.05), fontsize=7)
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_gantt_chart(cfg, run_schedule, capacity, title=None, save_path=None):
    hours = np.arange(24)
    n_levels = len(run_schedule)

    fig, axes = plt.subplots(n_levels, 1, figsize=(7.2, 1.1 * n_levels + 0.3), sharex=True)
    if n_levels == 1:
        axes = [axes]

    for idx, (cap, sched) in enumerate(zip(capacity, run_schedule)):
        ax = axes[idx]
        for h in hours:
            p = cfg.price_buy[int(h)]
            if p == 0.3424:
                c = '#C8E6C9'
            elif p == 0.6074:
                c = '#FFF9C4'
            else:
                c = '#FFCDD2'
            ax.axvspan(h - 0.5, h + 0.5, facecolor=c, alpha=0.7)

        for h, running in enumerate(sched):
            if running:
                ax.barh(0, 1, left=h - 0.45, height=0.5, color='#4A7FB5',
                        alpha=0.85, edgecolor='white', linewidth=0.3)

        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(-0.6, 0.6)
        ax.set_yticks([])
        ax.set_ylabel(f'{cap} t/d', fontsize=12, fontweight='bold', labelpad=5)
        ax.grid(axis='x', alpha=0.15, linewidth=0.3)
        ax.tick_params(pad=1)

    # axes[0].set_title(title or '各产量最优生产时段', fontsize=10, fontweight='bold', pad=4)
    axes[-1].set_xlabel('时刻/h', fontsize=12, labelpad=5)
    axes[-1].set_xticks(hours)
    axes[-1].set_xticklabels([f'{int(h)}' for h in hours], fontsize=11)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#C8E6C9', label='谷(0.3424)'),
        Patch(facecolor='#FFF9C4', label='平(0.6074)'),
        Patch(facecolor='#FFCDD2', label='峰(0.8024)'),
        Patch(facecolor='#4A7FB5', label='运行'),
    ]
    ax = axes[0] if n_levels > 0 else axes
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11,
              ncol=4, framealpha=0.8, handlelength=1.2)

    plt.tight_layout(pad=0.3)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_cost_vs_production(production_levels, results, title='指标随产量变化',
                            save_path=None):
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))

    ax = axes[0]
    costs = [r['cost_per_ton'] for r in results]
    ax.plot(production_levels, costs, 'o-', color=SEMANTIC['load'], linewidth=1.5,
            markersize=4, markerfacecolor='white', markeredgewidth=1)
    min_idx = np.argmin(costs)
    ax.plot(production_levels[min_idx], costs[min_idx], '*', color=SEMANTIC['improve'],
            markersize=10, markeredgecolor='black', markeredgewidth=0.5,
            label=f'最低: {costs[min_idx]:.0f}元/吨')
    for i, (x, y) in enumerate(zip(production_levels, costs)):
        ax.annotate(f'{y:.0f}', (x, y), textcoords='offset points',
                    xytext=(0, 6), ha='center', fontsize=7)
    setup_ax(ax, '日产量/(t/d)', '吨氨成本/(元/吨)', '吨氨成本')
    ax.legend(fontsize=7)

    ax = axes[1]
    for key, color, label, req_val in [
        ('self_consume_ratio', '#7A9E9F', '自发自用比例', 0.6),
        ('green_ratio', '#D4B68A', '绿电比例', 0.3),
        ('curtail_ratio', '#CE7E7E', '上网比例', 0.2),
    ]:
        vals = [r['indicators'][key] for r in results]
        ax.plot(production_levels, vals, 'o-', color=color, linewidth=1.2,
                markersize=3.5, label=label)
        ax.axhline(y=req_val, color=color, linestyle='--', linewidth=0.6, alpha=0.6)
    setup_ax(ax, '日产量/(t/d)', '比例', '绿电直连指标')

    ax = axes[2]
    util_rates = [r['utilization_rate'] for r in results]
    ax.bar(production_levels, util_rates, width=4, color=SEMANTIC['alkel'],
           alpha=0.8, edgecolor='white', linewidth=0.3)
    for x, y in zip(production_levels, util_rates):
        ax.annotate(f'{y:.1%}', (x, y), textcoords='offset points',
                    xytext=(0, 5), ha='center', fontsize=7)
    setup_ax(ax, '日产量/(t/d)', '设备利用率', '制氢氨设备利用率')

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.02)
    plt.tight_layout(pad=0.5)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_24_scenarios_heatmap(scenario_ids, production_levels, cost_matrix,
                              title='24场景×5产量吨氨成本热力图', save_path=None):
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    im = ax.imshow(cost_matrix, aspect='auto', cmap='YlOrRd')

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('吨氨成本(元/吨)', fontsize=6.5)
    cbar.ax.tick_params(labelsize=5.5)

    ax.set_xticks(np.arange(len(production_levels)))
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=6)
    ax.set_yticks(np.arange(len(scenario_ids)))
    ax.set_yticklabels(scenario_ids, fontsize=5.5)

    for i in range(cost_matrix.shape[0]):
        for j in range(cost_matrix.shape[1]):
            val = cost_matrix[i, j]
            ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                    fontsize=5, color='white' if val > np.nanmean(cost_matrix) else 'black')

    ax.set_xlabel('日产量', fontsize=7)
    ax.set_ylabel('风光场景', fontsize=7)
    # ax.set_title(title, fontsize=7.5, fontweight='bold')

    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_scenario_compliance(counts_by_level, production_levels,
                              title='各产量绿电指标达标统计', save_path=None):
    fig, ax = plt.subplots(figsize=(6, 3))

    x = np.arange(len(production_levels))
    width = 0.5
    bottom = np.zeros(len(production_levels))
    categories = [
        ('全满足', 'all_pass', SEMANTIC['all_pass']),
        ('部分满足', 'partial_pass', SEMANTIC['partial_pass']),
        ('全不满足', 'no_pass', SEMANTIC['no_pass']),
    ]

    for label, key, color in categories:
        vals = [counts_by_level[l][key] for l in production_levels]
        bars = ax.bar(x, vals, width, bottom=bottom, label=label, color=color,
               alpha=0.8, edgecolor='white', linewidth=0.3)
        for i, v in enumerate(vals):
            if v > 0:
                ax.text(i, bottom[i] + v / 2, str(v), ha='center', va='center',
                        fontsize=8, fontweight='bold', color='white')
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=8)
    ax.set_xlabel('日产量', fontsize=8.5)
    ax.set_ylabel('场景数量', fontsize=8.5)
    # ax.set_title(title, fontsize=9, fontweight='bold')
    ax.legend(fontsize=7.5, loc='upper right')
    ax.set_ylim(0, 28)

    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_annual_cost_distribution(costs_by_level, production_levels,
                                  title='全年吨氨成本分布', save_path=None):
    n_levels = len(production_levels)
    fig, axes = plt.subplots(n_levels, 1, figsize=(6, 1.8 * n_levels), sharex=True)
    if n_levels == 1:
        axes = [axes]

    for idx, (ax, level) in enumerate(zip(axes, production_levels)):
        costs = costs_by_level[level]
        mean_val = np.mean(costs)
        std_val = np.std(costs)

        ax.hist(costs, bins=12, density=True, alpha=0.5,
                color=COLOR_LIST[idx % len(COLOR_LIST)], edgecolor='white', linewidth=0.2)

        x_smooth = np.linspace(min(costs), max(costs), 200)
        from scipy import stats
        kernel = stats.gaussian_kde(costs)
        ax.plot(x_smooth, kernel(x_smooth), '-', color=COLOR_LIST[idx % len(COLOR_LIST)],
                linewidth=1.2, label='概率密度')

        ax.axvline(mean_val, color='#C48080', linestyle='--', linewidth=0.8,
                   label=f'均值={mean_val:.0f}')
        ax.axvline(mean_val - std_val, color='#999999', linestyle=':', linewidth=0.6)
        ax.axvline(mean_val + std_val, color='#999999', linestyle=':', linewidth=0.6)

        ax.set_ylabel('概率', fontsize=7.5)
        ax.set_title(f'{level} t/d', fontsize=8.5, fontweight='bold')
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.12)

    axes[-1].set_xlabel('吨氨成本/(元/吨)', fontsize=8.5)
    # fig.suptitle(title, fontsize=7.5, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.3)

    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_comparison_q2_q3(production_levels, q2_costs, q3_costs, q2_indicators, q3_indicators,
                                                     title='Q2与Q3对比分析', save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))

    ax = axes[0]
    x = np.arange(len(production_levels))
    w = 0.35
    bars1 = ax.bar(x - w / 2, q2_costs, w, label='离散(Q2)', color=SEMANTIC['load'], alpha=0.8, linewidth=0.3)
    bars2 = ax.bar(x + w / 2, q3_costs, w, label='连续(Q3)', color=SEMANTIC['wind'], alpha=0.8, linewidth=0.3)

    for i in range(len(production_levels)):
        improvement = (q2_costs[i] - q3_costs[i]) / q2_costs[i] * 100
        ax.annotate(f'{improvement:.1f}%', (x[i], max(q2_costs[i], q3_costs[i])),
                    textcoords='offset points', xytext=(0, 5),
                    ha='center', fontsize=7, fontweight='bold',
                    color='#3A6B6B' if improvement > 0 else '#B06060')

    ax.set_xticks(x)
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=8)
    setup_ax(ax, '日产量', '吨氨成本/(元/吨)', '吨氨成本对比')

    ax = axes[1]
    metrics_config = [
        ('self_consume_ratio', '#7A9E9F', '自发自用比例', 0.6),
        ('green_ratio', '#D4B68A', '绿电比例', 0.3),
        ('curtail_ratio', '#CE7E7E', '上网比例', 0.2),
    ]
    x = np.arange(len(production_levels))

    for key, color, label, threshold in metrics_config:
        q2_vals = [q2_indicators[l][key] for l in production_levels]
        q3_vals = [q3_indicators[l][key] for l in production_levels]
        ax.plot(x, q2_vals, 'o-', color=color, linewidth=1.2, markersize=3.5,
                label=f'{label}(Q2)', alpha=0.7)
        ax.plot(x, q3_vals, 's--', color=color, linewidth=1.2, markersize=3.5,
                label=f'{label}(Q3)', alpha=0.9)
        ax.axhline(y=threshold, color=color, linestyle=':', linewidth=0.5, alpha=0.4)

    ax.set_xticks(x)
    ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=7.5)
    ax.set_xlabel('日产量/(t/d)', fontsize=8.5)
    ax.set_ylabel('比例', fontsize=8.5)
    ax.set_title('Q2与Q3绿电指标', fontsize=9, fontweight='bold')
    ax.legend(fontsize=5.5, ncol=3, handlelength=1.2)
    ax.grid(True, alpha=0.12)

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.02)
    plt.tight_layout(pad=0.5)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_sankey_diagram(values, labels, title='能量流向桑基图', save_path=None):
    try:
        import matplotlib.sankey as sankey
        fig, ax = plt.subplots(figsize=(5, 3))
        sankey.Sankey(ax=ax, unit='MWh', format='%.1f',
                      scale=0.01, offset=0.2, head_angle=120).add(
            flows=values,
            labels=labels,
            orientations=[0, 0, 1, -1, 0, 0],
            pathlengths=[0.5]*len(values),
            colors=[SEMANTIC[c] for c in ['wind', 'solar', 'load', 'alkel', 'sell', 'buy']]
        ).finish()
        # ax.set_title(title, fontsize=7.5, fontweight='bold')
        plt.tight_layout()
        if save_path:
            save_fig(fig, save_path)
        return fig
    except:
        fig, ax = plt.subplots(figsize=(5, 3))
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=[SEMANTIC[c] for c in ['wind', 'solar', 'load', 'alkel', 'sell', 'buy']],
            startangle=90, explode=[0.02]*len(values),
            textprops={'fontsize': 7.5}
        )
        for t in autotexts:
            t.set_fontsize(7)
        # ax.set_title(title, fontsize=7.5, fontweight='bold')
        plt.tight_layout()
        if save_path:
            save_fig(fig, save_path)
        return fig

def plot_pareto_storage(storage_caps, costs, curtail_rates,
                        title='储能容量优化Pareto曲线', save_path=None):
    fig, ax1 = plt.subplots(figsize=(5, 3))

    ax1.plot(storage_caps, costs, 'o-', color=SEMANTIC['wind'], linewidth=1.5,
             markersize=4, markerfacecolor='white', markeredgewidth=1,
             label='吨氨成本')
    ax1.set_xlabel('储能容量/MWh', fontsize=8.5)
    ax1.set_ylabel('吨氨成本/(元/吨)', fontsize=8.5, color=SEMANTIC['wind'])
    ax1.tick_params(axis='y', labelcolor=SEMANTIC['wind'], labelsize=8)
    ax1.tick_params(axis='x', labelsize=8)

    ax2 = ax1.twinx()
    ax2.plot(storage_caps, curtail_rates, 's--', color=SEMANTIC['curtail'], linewidth=1.2,
             markersize=4, markerfacecolor='white', markeredgewidth=1,
             label='弃电率')
    ax2.set_ylabel('弃电率', fontsize=8.5, color=SEMANTIC['curtail'])
    ax2.tick_params(axis='y', labelcolor=SEMANTIC['curtail'], labelsize=8)

    knee_idx = np.argmin(np.abs(np.diff(costs) / np.maximum(np.diff(storage_caps), 1)))
    ax1.axvline(x=storage_caps[knee_idx], color='#999999', linestyle=':',
                linewidth=0.6, alpha=0.6)
    ax1.annotate(f'膝点: {storage_caps[knee_idx]:.1f} MWh',
                 xy=(storage_caps[knee_idx], costs[knee_idx]),
                 xytext=(storage_caps[knee_idx] * 1.3, costs[knee_idx] * 1.08),
                 fontsize=7, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='#999999', lw=0.6))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7)

    ax1.grid(True, alpha=0.12)
    # ax1.set_title(title, fontsize=7.5, fontweight='bold')

    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_soc_discharge(soc_data, ch_data, dis_data, hours, title='储能SOC与充放电功率',
                       save_path=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4), sharex=True)

    for key in soc_data:
        ax1.plot(hours, soc_data[key], '-', linewidth=1.2, label=key)
    ax1.set_ylabel('SOC/%', fontsize=8.5)
    ax1.set_title('荷电状态', fontsize=9, fontweight='bold')
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.12)
    ax1.set_ylim(0, 105)
    ax1.tick_params(labelsize=8)

    ax2.bar(hours, ch_data, label='充电', color=SEMANTIC['storage'], alpha=0.7, width=0.7, linewidth=0.2)
    ax2.bar(hours, -dis_data, label='放电', color=SEMANTIC['sell'], alpha=0.7, width=0.7, linewidth=0.2)
    ax2.axhline(y=0, color='black', linewidth=0.4)
    ax2.set_xlabel('时刻/h', fontsize=8.5)
    ax2.set_ylabel('功率/MW', fontsize=8.5)
    ax2.set_title('充放电功率', fontsize=9, fontweight='bold')
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.12)
    ax2.tick_params(labelsize=8)

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_offgrid_comparison(scenarios, with_storage_data, without_storage_data,
                            title='离网运行有无储能对比', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8))

    labels = [s['label'] for s in scenarios]
    x = np.arange(len(labels))

    ax = axes[0, 0]
    ax.bar(x - 0.2, without_storage_data['curtail_rates'], 0.35,
           label='无储能', color=SEMANTIC['load'], alpha=0.7, linewidth=0.2)
    ax.bar(x + 0.2, with_storage_data['curtail_rates'], 0.35,
           label='有储能', color=SEMANTIC['storage'], alpha=0.7, linewidth=0.2)
    setup_ax(ax, '场景', '弃电率', '弃电率')
    ax.legend(fontsize=7)
    ax.tick_params(axis='x', labelsize=7)

    ax = axes[0, 1]
    ax.bar(x - 0.2, without_storage_data['productions'], 0.35,
           label='无储能', color=SEMANTIC['load'], alpha=0.7, linewidth=0.2)
    ax.bar(x + 0.2, with_storage_data['productions'], 0.35,
           label='有储能', color=SEMANTIC['storage'], alpha=0.7, linewidth=0.2)
    setup_ax(ax, '场景', '产量/(t/d)', '日产量')
    ax.legend(fontsize=7)
    ax.tick_params(axis='x', labelsize=7)

    ax = axes[1, 0]
    ax.bar(x - 0.2, without_storage_data['util_rates'], 0.35,
           label='无储能', color=SEMANTIC['load'], alpha=0.7, linewidth=0.2)
    ax.bar(x + 0.2, with_storage_data['util_rates'], 0.35,
           label='有储能', color=SEMANTIC['storage'], alpha=0.7, linewidth=0.2)
    setup_ax(ax, '场景', '产能利用率', '产能利用率')
    ax.legend(fontsize=7)
    ax.tick_params(axis='x', labelsize=7)

    ax = axes[1, 1]
    ax.bar(x - 0.2, without_storage_data['re_util_rates'], 0.35,
           label='无储能', color=SEMANTIC['load'], alpha=0.7, linewidth=0.2)
    ax.bar(x + 0.2, with_storage_data['re_util_rates'], 0.35,
           label='有储能', color=SEMANTIC['storage'], alpha=0.7, linewidth=0.2)
    setup_ax(ax, '场景', '可再生利用率', '可再生利用率')
    ax.legend(fontsize=7)
    ax.tick_params(axis='x', labelsize=7)

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_offgrid_power_balance(hours, P_wind, P_pv, P_conv, P_prod, P_curtail,
                               title='离网运行功率平衡', save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8))

    ax = axes[0, 0]
    ax.plot(hours, P_wind, 'o-', label='风电', color=SEMANTIC['wind'], linewidth=1, markersize=2.5)
    ax.plot(hours, P_pv, 's-', label='光伏', color=SEMANTIC['solar'], linewidth=1, markersize=2.5)
    ax.plot(hours, P_conv + P_prod, '^-', label='总负荷', color=SEMANTIC['load'], linewidth=1, markersize=2.5)
    setup_ax(ax, '时刻/h', '功率/MW', '可再生出力与负荷')

    ax = axes[0, 1]
    ax.bar(hours, P_curtail, color=SEMANTIC['curtail'], alpha=0.8, width=0.7, linewidth=0.2)
    setup_ax(ax, '时刻/h', '弃电功率/MW', '弃电量')

    ax = axes[1, 0]
    ax.fill_between(hours, 0, P_prod, label='制氨功率', color=SEMANTIC['alkel'], alpha=0.5)
    ax.plot(hours, P_wind + P_pv - P_conv, '--', color='#999999', linewidth=0.8, label='可用功率')
    setup_ax(ax, '时刻/h', '功率/MW', '制氨功率跟随可再生出力')

    ax = axes[1, 1]
    total_avail = np.sum(P_wind + P_pv - P_conv)
    total_used = np.sum(P_prod)
    total_curtailed = np.sum(P_curtail)

    pie_vals = np.array([max(0, total_used), max(0, total_curtailed), max(0, -total_avail)])
    pie_vals = pie_vals[pie_vals > 0]
    pie_labels = ['自用', '弃电', '缺电'][:len(pie_vals)]
    pie_colors = [SEMANTIC['all_pass'], SEMANTIC['curtail'], SEMANTIC['buy']][:len(pie_vals)]
    wedges, texts, autotexts = ax.pie(pie_vals, labels=pie_labels,
            autopct='%1.1f%%',
            colors=pie_colors,
            startangle=90, textprops={'fontsize': 7.5})
    for t in autotexts:
        t.set_fontsize(7)
    ax.set_title('能量分配', fontsize=9, fontweight='bold')

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_production_vs_curtailment(scenario_labels, productions, curtail_rates,
                                    title='各场景产量与弃电分析', save_path=None):
    fig, ax1 = plt.subplots(figsize=(7.2, 2.8))

    sort_idx = np.argsort(curtail_rates)[::-1]
    labels_sorted = [scenario_labels[i] for i in sort_idx]
    prods_sorted = [productions[i] for i in sort_idx]
    curtails_sorted = [curtail_rates[i] for i in sort_idx]

    x = np.arange(len(labels_sorted))
    bars = ax1.bar(x, prods_sorted, 0.6, label='日产量', color=SEMANTIC['alkel'], alpha=0.8, linewidth=0.2)
    ax1.set_ylabel('日产量/(t/d)', fontsize=8.5, color=SEMANTIC['alkel'])
    ax1.tick_params(axis='y', labelcolor=SEMANTIC['alkel'], labelsize=8)

    ax2 = ax1.twinx()
    ax2.plot(x, curtails_sorted, 'o-', color=SEMANTIC['curtail'], linewidth=1.2,
             markersize=3.5, label='弃电率')
    ax2.axhline(y=0.2, color=SEMANTIC['no_pass'], linestyle='--', linewidth=0.6, alpha=0.5)
    ax2.set_ylabel('弃电率', fontsize=8.5, color=SEMANTIC['curtail'])
    ax2.tick_params(axis='y', labelcolor=SEMANTIC['curtail'], labelsize=8)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_sorted, fontsize=7, rotation=45, ha='right')
    ax1.set_xlabel('场景', fontsize=8.5)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7.5)

    # ax1.set_title(title, fontsize=7.5, fontweight='bold')
    ax1.grid(True, alpha=0.12, axis='y')

    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_net_vs_offgrid_comparison(comparison_data, title='离网与联网模式经济性对比',
                                    save_path=None):
    metrics = ['吨氨成本', '净电费', '年产量', '能自给率']
    fig, ax = plt.subplots(figsize=(5, 2.8))

    x = np.arange(len(metrics))
    w = 0.35

    ongrid_vals = [comparison_data['ongrid'].get(m, 0) for m in metrics]
    offgrid_vals = [comparison_data['offgrid'].get(m, 0) for m in metrics]

    bars1 = ax.bar(x - w / 2, ongrid_vals, w, label='联网模式', color=SEMANTIC['wind'], alpha=0.8, linewidth=0.2)
    bars2 = ax.bar(x + w / 2, offgrid_vals, w, label='离网模式', color=SEMANTIC['storage'], alpha=0.8, linewidth=0.2)

    for i in range(len(metrics)):
        ratio = offgrid_vals[i] / ongrid_vals[i] * 100 if ongrid_vals[i] != 0 else 0
        ax.text(i, max(ongrid_vals[i], offgrid_vals[i]) * 1.05,
                f'{ratio:.0f}%', ha='center', fontsize=7.5, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=8)
    setup_ax(ax, '', '')
    ax.legend(fontsize=7)

    # fig.suptitle(title, fontsize=7.5, fontweight='bold', y=1.02)
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_policy_analysis(save_path=None):
    # single column width
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    ax = axes[0]
    impacts = ['调峰压力增大', '备用容量需求增加', '电能质量挑战',
               '促进新能源消纳', '降低系统碳排放', '推动储能技术发展']
    directions = [-1, -1, -1, 1, 1, 1]
    magnitudes = [0.85, 0.7, 0.6, 0.9, 0.95, 0.75]
    colors_impact = ['#E74C3C' if d < 0 else '#27AE60' for d in directions]
    y_pos = np.arange(len(impacts))

    ax.barh(y_pos, [d * m for d, m in zip(directions, magnitudes)],
            color=colors_impact, alpha=0.8, height=0.5, linewidth=0.2)
    for i, (imp, d, m) in enumerate(zip(impacts, directions, magnitudes)):
        label = f'{imp} ({abs(m):.0%})'
        ax.text(0.03 if d > 0 else -0.03, i, label,
                ha='left' if d > 0 else 'right', va='center',
                fontsize=7, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([])
    ax.set_xlim(-1.3, 1.3)
    ax.set_title('高渗透率对电网影响', fontsize=8.5, fontweight='bold')
    ax.text(-1.2, -0.5, '← 不利影响', fontsize=7, color='#E74C3C', fontweight='bold')
    ax.text(1.1, -0.5, '有利影响 →', fontsize=7, color='#27AE60', fontweight='bold')
    ax.grid(True, alpha=0.12, axis='x')
    ax.tick_params(labelsize=8)

    ax = axes[1]
    policies = ['完善市场机制', '配置储能', '智能调度', '政策激励', '技术研发']
    values = [0.88, 0.82, 0.75, 0.92, 0.78]
    bars = ax.barh(policies, values, color='#2980B9', alpha=0.8, height=0.5, linewidth=0.2)
    for i, v in enumerate(values):
        ax.text(v + 0.02, i, f'{v:.0%}', va='center', fontsize=7.5, fontweight='bold')
    ax.set_xlim(0, 1.1)
    ax.set_title('政策建议框架', fontsize=8.5, fontweight='bold')
    ax.grid(True, alpha=0.12, axis='x')
    ax.tick_params(labelsize=8)

    # fig.suptitle('绿电直连园区发展影响与政策建议', fontsize=8, fontweight='bold', y=1.02)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_compliance_comparison(production_levels, q2_counts, q3_counts,
                               title='Q2与Q3达标统计对比', save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)

    for idx, (ax, counts, label) in enumerate(zip(
            axes, [q2_counts, q3_counts], ['离散调节(Q2)', '连续调节(Q3)'])):
        x = np.arange(len(production_levels))
        w = 0.5
        bottom = np.zeros(len(production_levels))
        for key, color in [('all_pass', SEMANTIC['all_pass']),
                            ('partial_pass', SEMANTIC['partial_pass']),
                            ('no_pass', SEMANTIC['no_pass'])]:
            vals = [counts[l][key] for l in production_levels]
            bars = ax.bar(x, vals, w, bottom=bottom, color=color, alpha=0.8,
                   edgecolor='white', linewidth=0.3, label={'all_pass': '全满足',
                                                   'partial_pass': '部分满足',
                                                   'no_pass': '全不满足'}[key])
            for i, v in enumerate(vals):
                if v > 0:
                    ax.text(i, bottom[i] + v / 2, str(v), ha='center',
                            va='center', fontsize=8, fontweight='bold', color='white')
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels([f'{l} t/d' for l in production_levels], fontsize=7.5)
        ax.set_title(label, fontsize=8.5, fontweight='bold')
        ax.set_xlabel('日产量', fontsize=8)
        ax.tick_params(labelsize=7.5)
        if idx == 0:
            ax.set_ylabel('场景数量', fontsize=8)

    axes[0].legend(fontsize=7)
    # fig.suptitle(title, fontsize=7.5, fontweight='bold', y=1.02)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig

def plot_q3_power_schedule(hours, P_wind, P_pv, P_conv, P_prod_continuous,
                           P_prod_discrete, P_buy, P_sell, title='连续调节功率调度方案',
                           save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8))

    ax = axes[0, 0]
    ax.fill_between(hours, 0, P_prod_continuous, label='连续制氨功率',
                    color=SEMANTIC['alkel'], alpha=0.45)
    ax.plot(hours, P_wind + P_pv - P_conv, '--', color='#999999', linewidth=0.8,
            label='可用功率')
    setup_ax(ax, '时刻/h', '功率/MW', '连续可调功率方案')

    ax = axes[0, 1]
    ax.step(hours, P_prod_discrete, where='mid', label='离散(Q2)', color=SEMANTIC['load'],
            linewidth=1.2)
    ax.fill_between(hours, 0, P_prod_continuous, label='连续(Q3)',
                    color=SEMANTIC['wind'], alpha=0.3)
    setup_ax(ax, '时刻/h', '功率/MW', '连续和离散调度对比')

    ax = axes[1, 0]
    ax.bar(hours, P_buy, label='购电', color=SEMANTIC['buy'], alpha=0.8, width=0.7, linewidth=0.2)
    ax.bar(hours, -P_sell, label='售电', color=SEMANTIC['sell'], alpha=0.8, width=0.7, linewidth=0.2)
    ax.axhline(y=0, color='black', linewidth=0.4)
    setup_ax(ax, '时刻/h', '功率/MW', '购电与售电')

    ax = axes[1, 1]
    equiv_load = P_conv + P_prod_continuous
    ax.stackplot(hours, [P_wind, P_pv], labels=['风电', '光伏'],
                 colors=[SEMANTIC['wind'], SEMANTIC['solar']], alpha=0.65)
    ax.plot(hours, equiv_load, '-', color=SEMANTIC['load'], linewidth=1, label='等效总负荷')
    setup_ax(ax, '时刻/h', '功率/MW', '可再生发电与等效负荷')

    # fig.suptitle(title, fontsize=8, fontweight='bold', y=1.01)
    plt.tight_layout(pad=0.4)
    if save_path:
        save_fig(fig, save_path)
    return fig
