"""
Replikasi diagnostik panel — Soft Power & Ketahanan Ekspor (Python, setara-STATA)
Disusun oleh Emaridial Ulza.

Memuat em_analysis.csv lalu mereproduksi:
  (1) Uji ketergantungan lintas-seksi Pesaran CD
  (2) Uji akar unit panel Fisher-ADF (level & diferensi pertama)
  (3) Koefisien koreksi kesalahan (ECT) dari DFE-ARDL error-correction
      dengan standard error Driscoll-Kraay

Jalankan:
    pip install pandas numpy scipy statsmodels linearmodels
    python replikasi.py
"""
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")
DF = pd.read_csv("em_analysis.csv").sort_values(["panelid", "year"])


# ---------- (1) Uji Pesaran CD ----------
def pesaran_cd(df, var, idc="panelid", tc="year"):
    w = df.pivot(index=tc, columns=idc, values=var)
    cols = [c for c in w.columns if w[c].notna().sum() > 2]
    w = w[cols]
    N = len(cols)
    s = 0.0
    for a in range(N):
        for b in range(a + 1, N):
            xi, xj = w.iloc[:, a].values, w.iloc[:, b].values
            m = np.isfinite(xi) & np.isfinite(xj)
            T = m.sum()
            if T > 2:
                r = np.corrcoef(xi[m], xj[m])[0, 1]
                if np.isfinite(r):
                    s += np.sqrt(T) * r
    cd = np.sqrt(2.0 / (N * (N - 1))) * s
    return cd, 2 * (1 - stats.norm.cdf(abs(cd)))


# ---------- (2) Uji akar unit Fisher-ADF (Maddala-Wu) ----------
def fisher_adf(df, var, diff=False):
    ps = []
    for _, sub in df.groupby("panelid"):
        s = sub.sort_values("year")[var].dropna().values.astype(float)
        if diff:
            s = np.diff(s)
        if len(s) < 6 or np.std(s) < 1e-9:
            continue
        try:
            p = adfuller(s, maxlag=1, regression="c", autolag=None)[1]
            ps.append(min(max(p, 1e-6), 0.999999))
        except Exception:
            pass
    N = len(ps)
    chi = -2 * np.sum(np.log(ps))
    return chi, 1 - stats.chi2.cdf(chi, 2 * N)


# ---------- (3) ECT dari DFE-ARDL error-correction (Driscoll-Kraay) ----------
def ect(df, dv, shock, exp_term, cush_term,
        controls=("z_fuelnet", "z_gov", "z_lgdp", "z_nbrand")):
    d = df.set_index(["panelid", "year"]).copy()
    g = d.groupby(level=0)
    lag = lambda c: g[c].shift(1)
    dif = lambda c: d[c] - g[c].shift(1)
    d["d_y"], d["L_y"] = dif(dv), lag(dv)
    longrun = list(controls) + [shock, exp_term, cush_term]
    cols = ["L_y"]
    for v in longrun:
        d["L_" + v], d["d_" + v] = lag(v), dif(v)
        cols += ["L_" + v, "d_" + v]
    sub = d[["d_y"] + cols].dropna()
    m = PanelOLS(sub["d_y"], sub[cols], entity_effects=True).fit(cov_type="kernel")
    return m.params["L_y"], m.std_errors["L_y"], m.pvalues["L_y"]


if __name__ == "__main__":
    print("=== (1) Uji ketergantungan lintas-seksi (Pesaran CD) ===")
    for lab, v in [("Ekspor", "exports_pct_gdp"), ("Soft power", "nbrand_res"),
                   ("GPR", "gpr_global"), ("Brent", "brent"), ("GSCPI", "gscpi"),
                   ("Eksposur energi", "fuel_net"), ("Volatilitas", "stock_vol"),
                   ("log PDB/kapita", "log_gdp_pc"), ("Tata kelola", "gov_index")]:
        cd, p = pesaran_cd(DF, v)
        print(f"{lab:18s} CD={cd:7.2f}  p={p:.4g}")

    print("\n=== (2) Uji akar unit panel Fisher-ADF (chi2, p) ===")
    for lab, v in [("Ekspor", "exports_pct_gdp"), ("Volatilitas", "stock_vol"),
                   ("Soft power", "nbrand_res"), ("Eksposur energi", "fuel_net"),
                   ("GPR", "gpr_global"), ("Brent", "brent"), ("GSCPI", "gscpi"),
                   ("log PDB/kapita", "log_gdp_pc"), ("Tata kelola", "gov_index")]:
        lc, lp = fisher_adf(DF, v, False)
        dc, dp = fisher_adf(DF, v, True)
        print(f"{lab:18s} level={lc:7.2f} (p={lp:.3g})   diff={dc:7.2f} (p={dp:.3g})")

    print("\n=== (3) ECT dari DFE-ARDL EC (SE Driscoll-Kraay) ===")
    for lab, sh, ex, cu in [("GPR", "z_gpr", "exp_gpr", "cush_gpr"),
                            ("Brent", "z_brent", "exp_brent", "cush_brent"),
                            ("GSCPI", "z_gscpi", "exp_gscpi", "cush_gscpi")]:
        b, se, p = ect(DF, "exports_pct_gdp", sh, ex, cu)
        print(f"Ekspor — {lab:6s} ECT={b:7.3f}  SE={se:.3f}  p={p:.3g}")
    b, se, p = ect(DF, "stock_vol", "z_gpr", "exp_gpr", "cush_gpr")
    print(f"Volatilitas    ECT={b:7.3f}  SE={se:.3f}  p={p:.3g}")
