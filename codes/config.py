import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures')
TBL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables')

HOURS = np.arange(24)
TIME_LABELS = [f'{h}:00-{h+1}:00' for h in range(24)]

def read_attach1():
    path = os.path.join(DATA_DIR, '附件1：园区典型日常规电负荷标幺功率曲线.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1, names=['时段', '标幺功率'])
    return df['标幺功率'].values

def read_attach2():
    path = os.path.join(DATA_DIR, '附件2：典型日风电、光伏标幺功率表.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1, names=['时段', '风电标幺', '光伏标幺'])
    return df['风电标幺'].values, df['光伏标幺'].values

def read_attach3():
    path = os.path.join(DATA_DIR, '附件3：园区6种场景的风电标幺功率表.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1)
    cols = [c for c in df.columns if c != 0]
    n_scenarios = len(cols)
    wind_scenarios = np.zeros((24, n_scenarios))
    for i, c in enumerate(cols):
        wind_scenarios[:, i] = df[c].values
    return wind_scenarios

def read_attach4():
    path = os.path.join(DATA_DIR, '附件4：园区4种场景的光伏标幺功率表.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1)
    cols = [c for c in df.columns if c != 0]
    n_scenarios = len(cols)
    pv_scenarios = np.zeros((24, n_scenarios))
    for i, c in enumerate(cols):
        pv_scenarios[:, i] = df[c].values
    return pv_scenarios

def read_attach5():
    path = os.path.join(DATA_DIR, '附件5：风光发电与制氢设备技术参数.xlsx')
    df = pd.read_excel(path, header=None)
    params = {}
    for _, row in df.iterrows():
        key = str(row.iloc[0]).strip()
        vals = row.iloc[1:].values
        params[key] = vals
    return params

def read_attach6():
    path = os.path.join(DATA_DIR, '附件6：储能设备和合成氨装置技术参数.xlsx')
    df = pd.read_excel(path, header=None)
    params = {}
    for _, row in df.iterrows():
        key = str(row.iloc[0]).strip()
        vals = row.iloc[1:].values
        params[key] = vals
    return params

def read_attach7():
    path = os.path.join(DATA_DIR, '附件7：分时电价表.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1, names=['时段', '电价'])
    return df

def read_attach8():
    path = os.path.join(DATA_DIR, '附件8：风电、光伏余电上网电价.xlsx')
    df = pd.read_excel(path, header=None, skiprows=1, names=['电源类型', '上网电价', '说明'])
    return df

def build_electricity_price():
    price = np.zeros(24)
    price[0:7] = 342.4
    price[7:10] = 607.4
    price[10:15] = 802.4
    price[15:16] = 607.4
    price[16:17] = 607.4
    price[17:18] = 607.4
    price[18:21] = 802.4
    price[21:23] = 607.4
    price[23:24] = 342.4
    return price

class Config:
    def __init__(self):
        self.load_curve = read_attach1()
        self.wind_typical, self.pv_typical = read_attach2()
        self.wind_scenarios = read_attach3()
        self.pv_scenarios = read_attach4()
        self.price_buy = build_electricity_price()
        price_df = read_attach8()
        self.price_sell = 377.9
        self.equip_params = read_attach5()
        self.storage_params = read_attach6()

        self.P_wind_MW = 40.0
        self.P_pv_MW = 64.0
        self.P_load_peak_MW = 6.0

        self.alkel_power_MW = 10.0
        self.alkel_h2_kgh = 140.0
        self.pemel_power_MW = 10.0
        self.pemel_h2_kgh = 160.0
        self.nh3_power_MW = 0.75
        self.nh3_rate_th = 1.5
        self.nh3_h2_consumption = 0.2
        self.nh3_elec_consumption = 0.5

        self.wind_cost = 150.0
        self.pv_cost = 120.0
        self.alkel_om = 100.0
        self.pemel_om = 150.0
        self.nh3_om = 2.0
        self.storage_om = 10.0

        self.storage_inv = 1000.0
        self.storage_life = 15
        self.storage_ch_eff = 0.90
        self.storage_dis_eff = 0.90
        self.storage_self_discharge = 0.002

        self.nh3_inv = 60000.0
        self.equip_life = 30

        self.days_per_scenario = 15
        self.annual_days = 360

        self.REQUIRE_SELF_CONSUME = 0.60
        self.REQUIRE_GREEN_RATIO = 0.30
        self.REQUIRE_CURTAIL_RATIO = 0.20

        self._typical_power()

    def _typical_power(self):
        self.P_conv = self.P_load_peak_MW * self.load_curve
        self.P_wind_typ = self.P_wind_MW * self.wind_typical
        self.P_pv_typ = self.P_pv_MW * self.pv_typical

    def get_production_power(self, capacity_tpd):
        scale = capacity_tpd / 36.0
        return {
            'alkel': self.alkel_power_MW * scale,
            'pemel': self.pemel_power_MW * scale,
            'nh3': self.nh3_power_MW * scale,
            'total': (self.alkel_power_MW + self.pemel_power_MW + self.nh3_power_MW) * scale,
            'h2_rate_kgh': (self.alkel_h2_kgh + self.pemel_h2_kgh) * scale,
            'nh3_rate_th': self.nh3_rate_th * scale
        }

    def get_nh3_per_hour(self, capacity_tpd):
        scale = capacity_tpd / 36.0
        return self.nh3_rate_th * scale

def generate_scenarios(cfg):
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
                'P_re': p_wind + p_pv
            })
    return scenarios

if __name__ == '__main__':
    cfg = Config()
    print('Conventional load (24h):', cfg.P_conv)
    print('Typical wind (24h):', cfg.P_wind_typ)
    print('Typical solar (24h):', cfg.P_pv_typ)
    print('Electricity price (24h):', cfg.price_buy)
    print('Sell price:', cfg.price_sell)
    scens = generate_scenarios(cfg)
    print(f'Total scenarios: {len(scens)}')
    print('Scenario 1 wind:', scens[0]['P_wind'][:3])
    print('Scenario 1 solar:', scens[0]['P_pv'][:3])
