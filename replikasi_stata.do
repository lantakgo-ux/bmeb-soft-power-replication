* =====================================================================
* Replikasi diagnostik panel — Soft Power & Ketahanan Ekspor (STATA)
* Disusun oleh Emaridial Ulza.
*
* Do-file ini adalah PADANAN STATA dari pipeline analisis. Mesin estimasi
* yang sebenarnya dijalankan dalam Python (lihat replikasi.py); berkas ini
* disediakan sebagai dokumentasi/rujukan bagi pengguna STATA.
*
* Paket yang diperlukan:
*   ssc install xtcd2
*   ssc install xtscc
*   ssc install pvar
* =====================================================================

import delimited "em_analysis.csv", clear
xtset panelid year

* ---------------------------------------------------------------------
* (1) Uji ketergantungan lintas-seksi (Pesaran CD)
* ---------------------------------------------------------------------
foreach v in exports_pct_gdp nbrand_res gpr_global brent gscpi ///
             fuel_net stock_vol log_gdp_pc gov_index {
    display _newline "CD: `v'"
    xtcd2 `v'
}

* ---------------------------------------------------------------------
* (2) Uji akar unit panel Fisher-ADF (level & diferensi pertama)
* ---------------------------------------------------------------------
foreach v in exports_pct_gdp stock_vol nbrand_res fuel_net gpr_global ///
             brent gscpi log_gdp_pc gov_index {
    display _newline "Fisher-ADF level: `v'"
    xtunitroot fisher `v', dfuller lags(1)
    display _newline "Fisher-ADF diff: `v'"
    xtunitroot fisher d.`v', dfuller lags(1)
}

* ---------------------------------------------------------------------
* (3) DFE-ARDL error-correction, SE Driscoll-Kraay (xtscc)
*     Bentuk EC satu langkah:
*       D.y = phi*L.y + b'*L.X + g'*D.X + efek tetap negara
*     Koefisien pada L.y adalah ECT (phi); diharapkan negatif-signifikan.
* ---------------------------------------------------------------------

* Spesifikasi GPR (DV = ketahanan ekspor)
xtscc d.exports_pct_gdp l.exports_pct_gdp ///
      l.(z_fuelnet z_gov z_lgdp z_nbrand z_gpr exp_gpr cush_gpr) ///
      d.(z_fuelnet z_gov z_lgdp z_nbrand z_gpr exp_gpr cush_gpr), fe

* Spesifikasi Brent
xtscc d.exports_pct_gdp l.exports_pct_gdp ///
      l.(z_fuelnet z_gov z_lgdp z_nbrand z_brent exp_brent cush_brent) ///
      d.(z_fuelnet z_gov z_lgdp z_nbrand z_brent exp_brent cush_brent), fe

* Spesifikasi GSCPI
xtscc d.exports_pct_gdp l.exports_pct_gdp ///
      l.(z_fuelnet z_gov z_lgdp z_nbrand z_gscpi exp_gscpi cush_gscpi) ///
      d.(z_fuelnet z_gov z_lgdp z_nbrand z_gscpi exp_gscpi cush_gscpi), fe

* Model volatilitas pasar finansial (DV = stock_vol)
xtscc d.stock_vol l.stock_vol ///
      l.(z_fuelnet z_gov z_lgdp z_nbrand z_gpr exp_gpr cush_gpr) ///
      d.(z_fuelnet z_gov z_lgdp z_nbrand z_gpr exp_gpr cush_gpr), fe

* ---------------------------------------------------------------------
* (4) Panel VAR split-sample (brand kuat vs lemah) + IRF
* ---------------------------------------------------------------------
* Contoh kerangka (sesuaikan ordering & lag sesuai naskah):
* foreach grp in 0 1 {
*     preserve
*     keep if brand_strong == `grp'
*     pvar exports_pct_gdp z_gpr z_nbrand, lags(1)
*     pvarirf, oirf step(10)
*     restore
* }
