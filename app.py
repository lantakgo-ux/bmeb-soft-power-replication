"""
Pengumpul Data — Soft Power & Ketahanan Ekspor Pasar Berkembang
Disusun oleh Emaridial Ulza.

Alat ini menarik dan merakit panel data sekunder (23 pasar berkembang, 2011-2024)
untuk studi soft power dan ketahanan ekspor. Jalankan secara lokal:

    pip install -r requirements.txt
    streamlit run app.py

Hanya FRED yang membutuhkan API key (gratis: https://fredaccount.stlouisfed.org/apikey).
World Bank tidak membutuhkan key. Sumber lain (Elcano, GPR, GSCPI, volatilitas saham)
diunggah sebagai CSV — lihat README.md untuk format dan tautan sumber.
"""
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Pengumpul Data — Soft Power & Ekspor", layout="wide")

# --- 23 pasar berkembang dalam studi (boleh diubah/diperluas) ---
COUNTRIES = {
    'ARG': 'Argentina', 'BRA': 'Brazil', 'BRN': 'Brunei', 'KHM': 'Cambodia',
    'CHL': 'Chile', 'COL': 'Colombia', 'EGY': 'Egypt', 'IND': 'India',
    'IDN': 'Indonesia', 'LAO': 'Laos', 'MYS': 'Malaysia', 'MEX': 'Mexico',
    'MMR': 'Myanmar', 'NGA': 'Nigeria', 'PAK': 'Pakistan', 'PHL': 'Philippines',
    'POL': 'Poland', 'SAU': 'Saudi Arabia', 'SGP': 'Singapore',
    'ZAF': 'South Africa', 'THA': 'Thailand', 'TUR': 'Turkey', 'VNM': 'Vietnam',
}

# --- Kode indikator World Bank (tanpa API key) ---
WB = {
    'exports_pct_gdp': 'NE.EXP.GNFS.ZS',   # Ekspor barang & jasa (% PDB)
    'gdp_pc_usd':      'NY.GDP.PCAP.CD',    # PDB per kapita (USD)
    'fuel_exp_pct':    'TX.VAL.FUEL.ZS.UN', # Ekspor bahan bakar (% ekspor barang)
    'fuel_imp_pct':    'TM.VAL.FUEL.ZS.UN', # Impor bahan bakar (% impor barang)
    'wgi_pv': 'PV.EST', 'wgi_ge': 'GE.EST', 'wgi_rq': 'RQ.EST',
    'wgi_rl': 'RL.EST', 'wgi_cc': 'CC.EST', 'wgi_va': 'VA.EST',  # enam estimasi WGI
}


@st.cache_data(show_spinner=False)
def fetch_wb(codes, indicator, y0, y1):
    """Menarik satu indikator World Bank untuk daftar negara. Tanpa API key."""
    url = f"https://api.worldbank.org/v2/country/{';'.join(codes)}/indicator/{indicator}"
    params = {"format": "json", "per_page": 20000, "date": f"{y0}:{y1}"}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    if len(js) < 2 or js[1] is None:
        return pd.DataFrame(columns=['iso3', 'year', 'value'])
    rows = [{'iso3': d['countryiso3code'], 'year': int(d['date']), 'value': d['value']}
            for d in js[1]]
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def fetch_fred_brent(key, y0, y1):
    """Menarik harga Brent harian dari FRED (butuh API key) dan merata-ratakan per tahun."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": "DCOILBRENTEU", "api_key": key, "file_type": "json",
              "observation_start": f"{y0}-01-01", "observation_end": f"{y1}-12-31"}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("observations", []))
    df = df[df['value'] != '.'].copy()
    df['value'] = df['value'].astype(float)
    df['year'] = pd.to_datetime(df['date']).dt.year
    return df.groupby('year')['value'].mean().rename('brent').reset_index()


def read_panel_csv(file, valuename):
    """Membaca CSV unggahan. Diharapkan kolom: iso3, year, value (panel) atau year, value (global)."""
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    if 'iso3' in df.columns:
        df = df.rename(columns={'value': valuename})[['iso3', 'year', valuename]]
    else:
        df = df.rename(columns={'value': valuename})[['year', valuename]]
    df['year'] = df['year'].astype(int)
    return df


def z(s):
    return (s - s.mean()) / s.std(ddof=0)


# ------------------------------------------------------------------ Sidebar
st.sidebar.header("Konfigurasi")
fred_key = st.sidebar.text_input("FRED API key", type="password",
                                 help="Gratis & instan di fredaccount.stlouisfed.org/apikey")
sel = st.sidebar.multiselect("Negara", options=list(COUNTRIES.keys()),
                             default=list(COUNTRIES.keys()),
                             format_func=lambda c: f"{c} — {COUNTRIES[c]}")
y0, y1 = st.sidebar.slider("Rentang tahun", 2000, 2024, (2011, 2024))

st.sidebar.markdown("**Unggah sumber non-API** (CSV; lihat README untuk format/sumber)")
up_soft = st.sidebar.file_uploader("Elcano — soft presence (iso3,year,value)", type="csv")
up_gprc = st.sidebar.file_uploader("GPR negara — GPRC (iso3,year,value)", type="csv")
up_gprg = st.sidebar.file_uploader("GPR global (year,value)", type="csv")
up_gscpi = st.sidebar.file_uploader("GSCPI (year,value)", type="csv")
up_vol = st.sidebar.file_uploader("Volatilitas saham (iso3,year,value)", type="csv")

run = st.sidebar.button("Rakit panel", type="primary")

# ------------------------------------------------------------------ Main
st.title("Pengumpul Data — Soft Power & Ketahanan Ekspor")
st.caption("Disusun oleh Emaridial Ulza · World Bank otomatis (tanpa key) · "
           "FRED butuh API key · sumber lain via unggahan CSV.")

if not run:
    st.info("Atur konfigurasi di panel kiri, lalu klik **Rakit panel**. "
            "Minimal World Bank akan ditarik; FRED & sumber lain ditambahkan bila tersedia.")
    st.stop()

if not sel:
    st.error("Pilih minimal satu negara."); st.stop()

# 1) World Bank
prog = st.progress(0.0, "Menarik data World Bank ...")
wide = None
for i, (name, code) in enumerate(WB.items()):
    df = fetch_wb(sel, code, y0, y1).rename(columns={'value': name})
    wide = df if wide is None else wide.merge(df, on=['iso3', 'year'], how='outer')
    prog.progress((i + 1) / len(WB), f"World Bank: {name}")
prog.empty()

panel = wide.copy()
panel['fuel_net'] = panel['fuel_exp_pct'] - panel['fuel_imp_pct']
panel['log_gdp_pc'] = np.log(panel['gdp_pc_usd'])
panel['gov_index'] = panel[[c for c in panel.columns if c.startswith('wgi_')]].mean(axis=1)

# 2) FRED Brent (global, by year)
if fred_key:
    try:
        brent = fetch_fred_brent(fred_key, y0, y1)
        panel = panel.merge(brent, on='year', how='left')
        st.success("Brent (FRED) ditambahkan.")
    except Exception as e:
        st.warning(f"FRED gagal ({e}). Lewati Brent.")
else:
    st.warning("Tanpa FRED API key — Brent dilewati.")

# 3) Sumber unggahan
def add_panel(up, col):
    global panel
    if up is None:
        return False
    d = read_panel_csv(up, col)
    panel = panel.merge(d, on=(['iso3', 'year'] if 'iso3' in d.columns else ['year']), how='left')
    return True

has_soft = add_panel(up_soft, 'soft_presence')
add_panel(up_gprc, 'gprc')
add_panel(up_gprg, 'gpr_global')
add_panel(up_gscpi, 'gscpi')
add_panel(up_vol, 'stock_vol')

# 4) Soft power residual (log soft presence ⊥ log PDB/kapita + tata kelola + FE tahun)
if has_soft:
    try:
        import statsmodels.formula.api as smf
        d = panel.dropna(subset=['soft_presence', 'log_gdp_pc', 'gov_index']).copy()
        d['log_soft'] = np.log(d['soft_presence'])
        m = smf.ols("log_soft ~ log_gdp_pc + gov_index + C(year)", data=d).fit()
        panel.loc[d.index, 'nbrand_res'] = m.resid
        st.success("Soft power (residual) dihitung.")
    except Exception as e:
        st.warning(f"Residualisasi soft power gagal: {e}")

# 5) Standardisasi + interaksi (shift-share & cushioning) bila variabel tersedia
for raw, zc in [('nbrand_res', 'z_nbrand'), ('fuel_net', 'z_fuelnet'), ('gprc', 'z_gpr'),
                ('brent', 'z_brent'), ('gscpi', 'z_gscpi'), ('gov_index', 'z_gov'),
                ('log_gdp_pc', 'z_lgdp')]:
    if raw in panel.columns:
        panel[zc] = z(panel[raw])
for sh in ['gpr', 'brent', 'gscpi']:
    if f'z_{sh}' in panel.columns and 'z_fuelnet' in panel.columns:
        panel[f'exp_{sh}'] = panel['z_fuelnet'] * panel[f'z_{sh}']     # jalur eksposur energi
    if f'z_{sh}' in panel.columns and 'z_nbrand' in panel.columns:
        panel[f'cush_{sh}'] = panel['z_nbrand'] * panel[f'z_{sh}']     # bantalan soft power

panel = panel.sort_values(['iso3', 'year']).reset_index(drop=True)

# ------------------------------------------------------------------ Output
st.subheader(f"Panel terakit — {panel['iso3'].nunique()} negara, "
             f"{panel['year'].min()}–{panel['year'].max()}, {len(panel)} observasi")
st.dataframe(panel, use_container_width=True, height=420)
st.download_button("Unduh panel (CSV)", panel.to_csv(index=False).encode('utf-8'),
                   file_name="em_analysis.csv", mime="text/csv")

with st.expander("Catatan & integritas"):
    st.markdown(
        "- Seluruh data berasal dari penyedia resmi; alat ini hanya **menarik & merakit**, "
        "tidak mengubah atau mengarang nilai.\n"
        "- Pemodelan ekonometrik, analisis, dan interpretasi dilakukan terpisah oleh penulis.\n"
        "- World Bank ditarik tanpa key; FRED memakai key yang Anda masukkan (tetap di mesin Anda).\n"
        "- Sumber Elcano/GPR/GSCPI/volatilitas diunggah sebagai CSV (lihat README)."
    )
