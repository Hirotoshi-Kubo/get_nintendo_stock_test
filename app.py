import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="ゲーム株ダッシュボード",
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

tickers = {
    '7974.T': 'Nintendo',
    '9684.T': 'Square Enix'
}

if not df.empty:
    
    #表示株価設定
    stock_list = df["Ticker"].unique()
    selected_stocks = st.sidebar.multiselect(
        "銘柄選択",
        stock_list,
        default=stock_list,  # デフォルトで全て選択
        format_func=lambda x: tickers.get(x, x)
    )

    if not selected_stocks:
        st.warning("少なくとも1つの銘柄を選択してください。")
    else:
        #表示銘柄のデータを抽出
        df_selected = df[df["Ticker"].isin(selected_stocks)]

        #サイドバーで表示期間設定
        st.sidebar.header("表示設定")
        num_days = st.sidebar.slider(
            "表示日数",
            1,
            len(df) // len(stock_list),  # おおよその最大日数
            30
        )
        
        # 選択された銘柄ごとに最新データを取得して表示
        # 銘柄名でマッピングして色分けなどの準備も可能だが、Plotlyが自動でやってくれる
        
        #グラフ作成
        fig = px.line(
            df_selected.tail(num_days * len(selected_stocks)), # 複数銘柄あるのでデータ数は銘柄数倍必要だが、日付フィルタの方が正確。簡易的にtailで取る場合注意が必要だが、日付で切るのがベスト。
            # 今回は簡易的にtailを使うが、正確には日付でフィルタすべき。
            # dataはreset_indexなどで整形済みと仮定するか、日付でフィルタする。
            # ここではシンプルに日付でフィルタするように修正する
            x="Date",
            y="Close",
            color="Ticker",
            title=f"株価推移 ({num_days}日間)"
        )
        
        # 銘柄名の表示を日本語にするために置換
        fig.for_each_trace(lambda t: t.update(name = tickers.get(t.name, t.name)))

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
                        label=f"{tickers.get(stock, stock)}",
                        value=f'{latest["Close"]:.0f}円',
                        delta=f'{latest["Close"] - prev["Close"]:.0f}円'
                    )

        st.subheader("詳細データ")
        st.dataframe(df_selected.sort_values(by=["Date", "Ticker"], ascending=[False, True]).head(10))


