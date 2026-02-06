import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="ゲーム株株価アプリ",
    page_icon="🎮",
    layout="wide"
)
st.title("ゲーム株価格推移ダッシュボード")

#DBからデータを取得
@st.cache_data(ttl=3600)    #1時間毎にDB読み込み
def load_data():
    conn = sqlite3.connect("nintendo_stock.db")
    df = pd.read_sql("SELECT * FROM stock_price ORDER BY Date ASC", conn)
    conn.close()
    return df

df = load_data()

if not df.empty:
    
    #表示株価設定
    stock_list = df["ticker"].unique()
    selected_stock = st.sidebar.selectbox(
        "銘柄選択",
        stock_list
    )

    #表示銘柄のデータを抽出
    df_selected = df[df["ticker"] == selected_stock]

    #サイドバーで表示期間設定
    st.sidebar.header("表示設定")
    num_days = st.sidebar.slider(
        "表示日数",
        1,
        len(df),
        30
    )
    #グラフ作成
    fig = px.line(
        df_selected.tail(num_days),
        x="Date",
        y="Close",
        title=f"{selected_stock}株価推移 ({num_days}日間)"
    )
    fig.update_traces(
        line=dict(
            color="red",
            width=2
        )
)

#画面表示
col1, col2 = st.columns([2,1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("最新データ")
    st.write(df.tail(5))

st.metric(
    label="最新株価",
    value=f'{df["Close"].iloc[-1]:.0f}円',
    delta=f'{df["Close"].iloc[-1] - df["Close"].iloc[-2]:.0f}円'
)


