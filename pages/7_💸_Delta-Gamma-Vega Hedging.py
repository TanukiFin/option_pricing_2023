import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt
import plotly.express as px
from scipy import log,exp,sqrt,stats
from scipy.stats import norm
import random
from myfunction import bsmodel
import warnings
warnings.filterwarnings("ignore")

# === 預設參數 ===
st.set_page_config(
    page_title="Delta-Gamma hedging",
    page_icon="📈",
    layout="wide",
)
st.header("Delta-Gamma-Vega hedging")
S0 = 50 # initial stock price
quantity = 100 # brokerage sales quantity ex. 100=賣100個

# === 打開網頁時，隨機跑一個股價 ===
if 'openweb' not in st.session_state:
    st.session_state.openweb = True
    df_St = bsmodel.get_GBM_St()
    st.session_state.df_St = df_St
    print("=== START ===")

# === 側邊 ===
with st.sidebar:
    st.markdown("**GBM模擬股價的參數**")
    steps_input = st.number_input("**steps =**", min_value=10,max_value=70,value=20)
    r_input = st.number_input("**r =**",min_value=0.0,max_value=0.1,value=0.05)
    sigma_input = st.number_input("**sigma =**", min_value=0.1,max_value=1.0,value=0.3)
    T_input = st.number_input("**T =**",min_value=0.1,max_value=2.0,value=1.0)
    # 按Simulate St 股價才會變動
    if st.button("Simulate St"):
        df_St = bsmodel.get_GBM_St(steps=steps_input, r=r_input, sigma=sigma_input, T=T_input)
        st.session_state.df_St = df_St # 暫存df
    st.markdown("此頁的股價產生方式為根據GBM隨機產生，每次點選網頁左側的[Simulate St]按鈕，即會根據所選參數產生新的隨機股價。")

# === Input區 ===
st.markdown("券商賣100個單位的選擇權，參數可調整的僅有履約價(K)、Type、Sell Price，其餘皆跟隨網頁左側的GBM參數。")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.success("**券商權證**")
    st.markdown("**S0 =** $50")
    K_A = st.number_input("**K =**",min_value=40,max_value=60,value=50)
    CP_A = st.selectbox(
    "Type: 券商要賣Call還是賣Put",
    ("Short Call","Short Put") )
    sell_price = st.number_input("Sell Price: 券商賣這個選擇權的售價，應高於理論價值(相當於成本)，這樣才有利潤",min_value=1,max_value=20,value=8)
    if CP_A=="Short Call": st.metric(label="option value at t=0", value=round(bsmodel.call(S0,K_A,r_input,sigma_input,T_input).price,2))
    if CP_A=="Short Put": st.metric(label="option value at t=0", value=round(bsmodel.put(S0,K_A,r_input,sigma_input,T_input).price,2))
    
with c2:
    st.success("**避險工具**")
    # B
    K_B = st.number_input("**Option B: K =**",min_value=40,max_value=60,value=48)
    CP_B = st.selectbox(
    "Option B: Type",
    ("Long Call","Long Put","Short Call","Short Put"), label_visibility ="collapsed" )
    # C
    K_C = st.number_input("**Option C: K =**",min_value=40,max_value=60,value=51)
    CP_C = st.selectbox(
    "Option C: Type",
    ("Long Call","Long Put","Short Call","Short Put"), label_visibility ="collapsed" )
  

st.info(f"""目前參數:　　:red[S0]={S0},　　:red[K]={K_A},　　:red[r]={r_input},　　:red[T]={round(T_input,2)},　　:red[sigma]={sigma_input} 
        \n 　　　　　　:red[type]={CP_A},　　:red[sell price]={sell_price}""")


df_price = bsmodel.get_greeks(st.session_state.df_St, K_list=[K_A,K_B,K_C], CP = [CP_A, CP_B, CP_C])   

# 股價 & Greek Letters圖 ==================================================================================
c1, c2 = st.columns(2, gap="large")
with c1:
    tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
    fig = px.line(df_price.round(2), x="t", y="St", title="Stock Price", height=300, template="plotly_white").update_layout(showlegend=False)
    tab1.plotly_chart(fig, use_container_width=True)
    tab2.write(df_price[["t","St"]].round(2),axis=1)

with c2:
    tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
    fig = px.line(df_price.round(2), x="t", y="A_Price", title=CP_A[6:10]+" Option Price", height=300, template="plotly_white").update_layout(showlegend=False)
    tab1.plotly_chart(fig, use_container_width=True)
    tab2.write(df_price[["t","A_Price"]].round(2).rename({"A_Price":"Option Price"},axis=1))


# 損益圖 ==================================================================================
tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
c1, c2 = tab1.columns([2,1], gap="large")
df_delta = bsmodel.get_delta_hedge(df_price, r_input, sigma_input, T_input, sell_price)
df_gamma = bsmodel.get_gamma_hedge(df_price, r_input, sigma_input, T_input, sell_price)
df_vega = bsmodel.get_vega_hedge(df_price, r_input, sigma_input, T_input, sell_price)
df_all_hedge = pd.DataFrame(columns=["t","No Hedging","Delta Hedging","Delta-Gamma Hedging","Delta-Gamma-Vega Hedging"])
df_all_hedge["t"] = df_delta["t"]
df_all_hedge["No Hedging"] = df_delta["Option_Profit"]
df_all_hedge["Delta Hedging"] = df_delta["Total_Profit"]
df_all_hedge["Delta-Gamma Hedging"] = df_gamma["Total_Profit"]
df_all_hedge["Delta-Gamma-Vega Hedging"] = df_vega["Total_Profit"]
with c2:
    st.markdown("Variable顯示")
    hedge_list = []
    cname = ["No Hedging","Delta Hedging","Delta-Gamma Hedging","Delta-Gamma-Vega Hedging"]
    cname2 = [" : 不避險的損益"," : 每期避險"," : 每五期避險(week0,week5,week10...)"," : 僅第一期避險"]
    for count in range(len(cname)):
        if st.checkbox(cname[count]+cname2[count],value=True):
            hedge_list.append(cname[count])
# 圖: 全部避險損益
fig = px.line(df_all_hedge.round(2), x="t", y=hedge_list, title="Delta Hedging", \
               labels={"value":"profit"},height=400, width=600, template="plotly_white") 
fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
))
with c1:
    st.plotly_chart(fig, use_container_width=True)
tab2.dataframe(df_delta)
# ===============================================================



# === greek letters ===
tab1, tab2 = st.tabs(["🗃 Greeks", "🗃 2"])
tab1.dataframe(df_price)

