import sys, os
import time

base = os.path.dirname(os.path.abspath(__file__))
if base not in sys.path:
    sys.path.insert(0, base)

from config import Config
import numpy as np

def main():
    print('=' * 70)
    print('绿电直连型电氢氨园区优化运行 - 全部分析')
    print('=' * 70)
    total_start = time.time()

    cfg = Config()

    print('\n' + '=' * 70)
    print('问题一：典型风光场景分析')
    print('=' * 70)
    t0 = time.time()
    from q1_simulation import run_q1, plot_q1_results, print_q1_results
    q1_results = run_q1()
    print_q1_results(q1_results, cfg)
    plot_q1_results(q1_results, cfg)
    print(f'  [完成 用时{time.time()-t0:.1f}s]')

    print('\n' + '=' * 70)
    print('问题二：离散制氨调节优化')
    print('=' * 70)
    t0 = time.time()
    from q2_scheduling import run_q2, plot_q2_results
    q2_data = run_q2()
    plot_q2_results(q2_data, cfg)
    print(f'  [完成 用时{time.time()-t0:.1f}s]')

    print('\n' + '=' * 70)
    print('问题三：连续制氨调节优化')
    print('=' * 70)
    t0 = time.time()
    from q3_continuous import run_q3, plot_q3_results
    q3_data = run_q3()
    plot_q3_results(q3_data, cfg, q2_data)
    print(f'  [完成 用时{time.time()-t0:.1f}s]')

    print('\n' + '=' * 70)
    print('问题四：离网运行及储能配置')
    print('=' * 70)
    t0 = time.time()
    from q4_offgrid import run_q4, plot_q4_results
    q4_data = run_q4()
    plot_q4_results(q4_data, cfg)
    print(f'  [完成 用时{time.time()-t0:.1f}s]')

    print('\n' + '=' * 70)
    print('问题五：政策分析')
    print('=' * 70)
    t0 = time.time()
    from q5_policy import print_q5_summary, plot_q5_results
    print_q5_summary()
    plot_q5_results()
    print(f'  [完成 用时{time.time()-t0:.1f}s]')

    print('\n' + '=' * 70)
    print('导出CSV结果文件')
    print('=' * 70)
    from save_csv import save_all
    save_all(q1_results, q2_data, q3_data, q4_data, cfg)

    total_time = time.time() - total_start
    print(f'\n 总计用时: {total_time:.1f}s')

    fig_dir = os.path.join(base, '..', 'figures')
    all_figs = []
    for root, dirs, files in os.walk(fig_dir):
        for f in files:
            if f.endswith('.pdf'):
                all_figs.append(os.path.relpath(os.path.join(root, f), fig_dir))
    tbl_dir = os.path.join(base, '..', 'tables')
    all_csvs = [f for f in os.listdir(tbl_dir) if f.endswith('.csv')] if os.path.isdir(tbl_dir) else []
    print(f'\n共生成 {len(all_figs)} 个图表文件 + {len(all_csvs)} 个CSV结果文件')
    for f in sorted(all_figs):
        print(f'  图 {f}')
    for f in sorted(all_csvs):
        print(f'  CSV {f}')

if __name__ == '__main__':
    main()
