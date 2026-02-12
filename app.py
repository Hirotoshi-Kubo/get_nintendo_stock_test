import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import timedelta
from config import TICKERS, DB_PATH

st.set_page_config(
    page_title="ゲーム株ダッシュボード",
    page_icon="🎮",
    layout="wide"
)
st.title("ゲーム株価格推移ダッシュボード")

#DBからデータを取得
@st.cache_data(ttl=3600)    #1時間毎にDB読み込み
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM stock_price ORDER BY Date ASC", conn)
    df["Date"] = pd.to_datetime(df["Date"])  # 日付型に変換
    return df

df = load_data()

if df.empty:
    st.error("データがありません。`python main.py` を実行してデータを取得してください。")
else:
    #表示株価設定
    stock_list = df["Ticker"].unique()
    selected_stocks = st.sidebar.multiselect(
        "銘柄選択",
        stock_list,
        default=stock_list,  # デフォルトで全て選択
        format_func=lambda x: TICKERS.get(x, x)
    )

    if not selected_stocks:
        st.warning("少なくとも1つの銘柄を選択してください。")
    else:
        #表示銘柄のデータを抽出
        df_selected = df[df["Ticker"].isin(selected_stocks)]

        #サイドバーで表示期間設定
        st.sidebar.header("表示設定")
        max_days = (df["Date"].max() - df["Date"].min()).days
        num_days = st.sidebar.slider(
            "表示日数",
            1,
            max(max_days, 1),
            min(30, max(max_days, 1))
        )
        
        # 日付でフィルタ（直近N日間）
        latest_date = df_selected["Date"].max()
        start_date = latest_date - timedelta(days=num_days)
        df_filtered = df_selected[df_selected["Date"] >= start_date]
        
        #グラフ作成
        fig = px.line(
            df_filtered,
            x="Date",
            y="Close",
            color="Ticker",
            title=f"株価推移 ({num_days}日間)"
        )
        
        # 銘柄名を日本語に置換 & ホバー設定
        fig.for_each_trace(lambda t: t.update(name = TICKERS.get(t.name, t.name)))
        fig.update_layout(hovermode="x unified")

        #画面表示
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("最新データ状況")
        
        # メトリクス表示（選択された銘柄分カラムを作成）
        cols = st.columns(len(selected_stocks))
        
        for i, stock in enumerate(selected_stocks):
            df_stock = df_selected[df_selected["Ticker"] == stock]
            if not df_stock.empty:
                latest = df_stock.iloc[-1]
                prev = df_stock.iloc[-2] if len(df_stock) > 1 else latest
                
                with cols[i]:
                    st.metric(
                        label=f"{TICKERS.get(stock, stock)}",
                        value=f'{latest["Close"]:.0f}円',
                        delta=f'{latest["Close"] - prev["Close"]:.0f}円'
                    )

        st.subheader("詳細データ")
        df_display = df_selected.sort_values(by=["Date", "Ticker"], ascending=[False, True]).head(10).copy()
        df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
        df_display["Ticker"] = df_display["Ticker"].map(TICKERS)
        df_display = df_display.rename(columns={"Date": "日付", "Ticker": "銘柄", "Close": "終値", "Volume": "出来高"})
        st.dataframe(df_display, hide_index=True)
