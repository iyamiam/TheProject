import streamlit as st
import pandas as pd
import altair as alt

# ============================================================
# 1. Fungsi untuk memuat data Indonesia + Jepang + Singapore
# ============================================================
@st.cache_data
def load_data_forecast(
    path_indonesia: str,
    path_jepang: str,
    path_singapore: str
) -> pd.DataFrame:
    # Load file CSV masing-masing negara
    df_idn = pd.read_csv(path_indonesia)
    df_jpn = pd.read_csv(path_jepang)
    df_sgp = pd.read_csv(path_singapore)

    # Normalisasi nama kolom agar konsisten
    rename_map = {
        "country": "COUNTRY",
        "Country": "COUNTRY",
        "COUNTRY": "COUNTRY",

        "indicator": "INDICATOR",
        "Indicator": "INDICATOR",
        "INDICATOR": "INDICATOR",

        "tahun": "TAHUN",
        "year": "TAHUN",
        "Year": "TAHUN",
        "TAHUN": "TAHUN",

        "value": "VALUE",
        "Value": "VALUE",
        "VALUE": "VALUE",

        "type": "TYPE",
        "Type": "TYPE",
        "TYPE": "TYPE",
    }

    data_list = [df_idn, df_jpn, df_sgp]

    for d in data_list:
        d.rename(columns=rename_map, inplace=True)

    # Jika kolom COUNTRY hilang → set manual per negara
    for d, default_country in zip(
        data_list,
        ["Indonesia", "Japan", "Singapore"]
    ):
        if "COUNTRY" not in d.columns:
            d["COUNTRY"] = default_country
        else:
            # Kalau ada tapi kosong semua, isi default country
            if d["COUNTRY"].isna().all():
                d["COUNTRY"] = default_country

    # Jika kolom TYPE hilang → default Actual
    for d in data_list:
        if "TYPE" not in d.columns:
            d["TYPE"] = "Actual"

    # Gabungkan ketiga negara
    df = pd.concat(data_list, ignore_index=True)

    # Pastikan tipe data benar
    df["TAHUN"] = pd.to_numeric(df["TAHUN"], errors="coerce").astype("Int64")
    df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")

    # Flag untuk garis forecast
    df["IS_FORECAST"] = df["TYPE"].str.lower() == "forecast"

    return df


# ============================================================
# 2. Konfigurasi Tampilan Streamlit (English UI)
# ============================================================
st.set_page_config(
    page_title="Country Forecast Dashboard 2000–2030 ",
    layout="wide"
)

st.title("📈 Country Forecast Dashboard")


# ============================================================
# 3. Load Data
# ============================================================
df = load_data_forecast(
    "data/DataIndonesiaForecast.csv",
    "data/DataJepangForecast.csv",
    "data/DataSingaporeForecast.csv"
)


# ============================================================
# 4. Sidebar Filter (English UI)
# ============================================================
st.sidebar.header("⚙️ Filters")

# Pilihan negara (maks 2 negara dalam visualisasi)
semua_negara = sorted(df["COUNTRY"].dropna().unique())
negara_dipilih = st.sidebar.multiselect(
    "Select Country (max 2)",
    options=semua_negara,
    default=semua_negara[:2]
)

# Validasi pemilihan negara
valid_negara = True
if len(negara_dipilih) == 0:
    st.sidebar.error("Please select at least one country.")
    valid_negara = False
elif len(negara_dipilih) > 2:
    st.sidebar.error("Maximum of two countries allowed.")
    valid_negara = False

# Pilihan indikator
semua_indikator = sorted(df["INDICATOR"].dropna().unique())
indikator_dipilih = st.sidebar.selectbox(
    "Select Indicator",
    options=semua_indikator
)

# Mode data
mode_data = st.sidebar.radio(
    "Data Type",
    ["Actual only", "Forecast only", "Actual + Forecast"],
    index=2
)

# Rentang tahun
tahun_min = int(df["TAHUN"].dropna().min())
tahun_max = int(df["TAHUN"].dropna().max())

rentang_tahun = st.sidebar.slider(
    "Year Range",
    min_value=tahun_min,
    max_value=tahun_max,
    value=(tahun_min, tahun_max),
    step=1
)


# ============================================================
# 5. Filter Data
# ============================================================
df_tampil = df.copy()

df_tampil = df_tampil[df_tampil["COUNTRY"].isin(negara_dipilih)]
df_tampil = df_tampil[df_tampil["INDICATOR"] == indikator_dipilih]

if mode_data == "Actual only":
    df_tampil = df_tampil[df_tampil["TYPE"].str.lower() == "actual"]
elif mode_data == "Forecast only":
    df_tampil = df_tampil[df_tampil["TYPE"].str.lower() == "forecast"]

df_tampil = df_tampil[
    (df_tampil["TAHUN"] >= rentang_tahun[0]) &
    (df_tampil["TAHUN"] <= rentang_tahun[1])
]


# ============================================================
# 6. Visualisasi
# ============================================================
if not valid_negara:
    st.warning("Please adjust the country selection.")
elif df_tampil.empty:
    st.warning("No data available for the selected filters.")
else:
    st.subheader("📊 Indicator Trend per Country")

    chart = (
        alt.Chart(df_tampil)
        .mark_line(point=True)
        .encode(
            x=alt.X("TAHUN:Q", title="Year", axis=alt.Axis(format=".0f")),
            y=alt.Y("VALUE:Q", title="Value"),
            color=alt.Color("COUNTRY:N", title="Country"),
            strokeDash=alt.condition(
                alt.datum.TYPE == "Forecast",
                alt.value([4, 4]),   # dashed = forecast
                alt.value([1, 0])    # solid = actual
            ),
            tooltip=[
                "COUNTRY",
                "INDICATOR",
                "TAHUN",
                alt.Tooltip("VALUE:Q", format=".2f"),
                "TYPE"
            ]
        )
        .properties(height=450)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


# ============================================================
# 7. Tabel Detail
# ============================================================
with st.expander("📄 View Data Table"):
    st.dataframe(
        df_tampil.sort_values(["COUNTRY", "TAHUN"]),
        use_container_width=True
    )
