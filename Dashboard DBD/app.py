import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="Dashboard DBD Kota Bima",
    layout="wide"
)

st.title("Dashboard Analisis dan Prediksi Kasus DBD Kota Bima")

# =============================
# STYLE
# =============================
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
[data-testid="stMetricValue"] { font-size: 35px; color: #ff4b4b; font-weight: bold; }
[data-testid="stSidebar"] { background-color: #f5f5f5; padding: 1.5rem 1rem; border-radius: 5px; box-shadow: 5px 5px 15px rgba(0,0,0,0.1); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #ff4b4b; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
[data-testid="stSidebar"] hr { border-top: 1px solid #ddd; }
[data-baseweb="select"] { border-radius: 5px !important; }
</style>
""", unsafe_allow_html=True)

# =============================
# LOAD LOGO
# =============================
logo_kotabima = Image.open("logo_kotabima.png")
st.sidebar.image(logo_kotabima, width=250)
st.sidebar.markdown("---")

# =============================
# FUNCTION: Load Data
# =============================
def load_data():
    df = pd.read_excel("data_dbd.xlsx", header=2)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
    df["jumlah_kasus_dbd"] = pd.to_numeric(df["jumlah_kasus_dbd"], errors="coerce")
    df["kode_wilayah"] = df["kode_wilayah"].astype(str)
    return df

df = load_data()

# =============================
# SIDEBAR MENU
# =============================
menu = st.sidebar.selectbox(
    "Pilih Halaman",
    ["Dashboard", "Upload Data", "Kelola Data"]
)

# =============================
# FUNCTION: Prediksi
# =============================
def buat_prediksi(df_input, tahun_ke_depan=6):
    train = df_input.groupby("tahun")["jumlah_kasus_dbd"].sum().reset_index()
    X = train[["tahun"]]
    y = train["jumlah_kasus_dbd"]
    model = LinearRegression()
    model.fit(X, y)
    tahun_terakhir = int(train["tahun"].max())
    future_years = pd.DataFrame({"tahun": np.arange(tahun_terakhir + 1, tahun_terakhir + 1 + tahun_ke_depan)})
    future_years["prediksi"] = model.predict(future_years)
    prediksi = pd.concat([train.rename(columns={"jumlah_kasus_dbd":"prediksi"}), future_years])
    return prediksi, tahun_terakhir + tahun_ke_depan

def tampilkan_prediksi(df_input, tahun_ke_depan=6):
    prediksi, akhir = buat_prediksi(df_input, tahun_ke_depan=tahun_ke_depan)
    st.subheader(f"Prediksi Kasus DBD Otomatis sampai {akhir}")
    fig_pred = px.line(
        prediksi,
        x="tahun",
        y="prediksi",
        markers=True,
        title=f"Prediksi Kasus DBD Otomatis sampai {akhir}"
    )
    st.plotly_chart(fig_pred, width='stretch', key=f'prediksi_{akhir}')
    

# =============================
# HALAMAN DASHBOARD
# =============================
if menu == "Dashboard":
    st.sidebar.title("Filter Data")

    tahun_list = sorted(df["tahun"].dropna().unique())
    tahun = st.sidebar.multiselect("Pilih Tahun", options=tahun_list, default=tahun_list)
    kecamatan = st.sidebar.multiselect("Pilih Kecamatan", options=df["nama_kecamatan"].dropna().unique(),
                                       default=df["nama_kecamatan"].dropna().unique())

    df_filter = df[(df["tahun"].isin(tahun)) & (df["nama_kecamatan"].isin(kecamatan))]

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Kasus DBD", int(df_filter["jumlah_kasus_dbd"].sum()))
    col2.metric("Total Kematian", int(df_filter["jumlah_kematian_dbd"].sum()))
    col3.metric("Jumlah Kecamatan", df_filter["nama_kecamatan"].nunique())

    # Tabel
    st.subheader("Data Kasus DBD")
    st.dataframe(df_filter, width='stretch')

    # Trend Kasus
    trend = df_filter.groupby("tahun")["jumlah_kasus_dbd"].sum().reset_index()
    fig_trend = px.line(trend, x="tahun", y="jumlah_kasus_dbd", markers=True, title="Tren Kasus DBD per Tahun")
    st.plotly_chart(fig_trend, width='stretch', key='trend_kasus')

    # Heatmap
    st.subheader("Heatmap Kasus DBD per Kecamatan dan Tahun")
    heat_data = df.pivot_table(values="jumlah_kasus_dbd", index="nama_kecamatan", columns="tahun", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(heat_data, cmap="Reds", linewidths=0.5, annot=True, fmt=".0f", ax=ax)
    st.pyplot(fig)

    # Peta Risiko
    st.subheader("Peta Risiko Kasus DBD per Kecamatan")
    geo = gpd.read_file("kecamatan_bima.geojson")
    map_data = df.groupby("nama_kecamatan")["jumlah_kasus_dbd"].sum().reset_index()
    geo["NAME_3"] = geo["NAME_3"].str.upper()
    map_data["nama_kecamatan"] = map_data["nama_kecamatan"].str.upper()
    geo = geo.merge(map_data, left_on="NAME_3", right_on="nama_kecamatan")
    m = folium.Map(location=[-8.45,118.72], zoom_start=11)
    folium.Choropleth(
        geo_data=geo,
        data=geo,
        columns=["NAME_3","jumlah_kasus_dbd"],
        key_on="feature.properties.NAME_3",
        fill_color="YlOrRd",
        legend_name="Jumlah Kasus DBD"
    ).add_to(m)
    st_folium(m, width=900)

    # Prediksi sampai 2030
    tahun_terakhir = int(df["tahun"].max())
    tahun_ke_depan = 2030 - tahun_terakhir
    if tahun_ke_depan > 0:
        tampilkan_prediksi(df, tahun_ke_depan=tahun_ke_depan)

    # Bar Chart
    st.subheader("Kasus DBD per Kecamatan")
    kecamatan_chart = df_filter.groupby("nama_kecamatan")["jumlah_kasus_dbd"].sum().reset_index()
    fig_bar = px.bar(kecamatan_chart, x="nama_kecamatan", y="jumlah_kasus_dbd",
                     color="jumlah_kasus_dbd", title="Distribusi Kasus DBD per Kecamatan")
    st.plotly_chart(fig_bar, width='stretch', key='bar_kecamatan')

# =============================
# HALAMAN UPLOAD DATA
# =============================
elif menu == "Upload Data":
    st.header("Upload Data DBD Baru")
    file_baru = st.file_uploader("Upload file Excel data terbaru", type=["xlsx"])
    if file_baru is not None:
        df_baru = pd.read_excel(file_baru, header=2)
        df_baru.columns = df_baru.columns.str.strip().str.lower().str.replace(" ", "_")
        df_gabung = pd.concat([df, df_baru], ignore_index=True)
        df_gabung.to_excel("data_dbd.xlsx", index=False)
        st.success("Data berhasil ditambahkan!")
        st.info("Silakan refresh halaman Dashboard untuk melihat data terbaru.")

# =============================
# HALAMAN KELOLA DATA
# =============================
elif menu == "Kelola Data":
    st.header("Kelola Data DBD")
    st.subheader("Data Saat Ini")
    st.dataframe(df)

    st.subheader("Hapus Data Berdasarkan Tahun")
    tahun_hapus = st.selectbox("Pilih Tahun yang ingin dihapus", sorted(df["tahun"].dropna().unique()))
    if st.button("Hapus Data Tahun Ini"):
        df_baru = df[df["tahun"] != tahun_hapus]
        df_baru.to_excel("data_dbd.xlsx", index=False)
        st.success(f"Data tahun {tahun_hapus} berhasil dihapus!")
        st.info("Silakan refresh halaman Dashboard untuk melihat data terbaru.")
