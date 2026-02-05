import sqlite3
import yfinance as yf
import pandas as pd

def update_nintendo_db():
    #任天堂株価取得
    ticker = "7974.T"
    df = yf.Ticker(ticker).history(period="5d")[['Close', 'Volume']]
    df.index.name = 'Date'

    #DB接続
    conn = sqlite3.connect("nintendo_stock.db")
    cur = conn.cursor()
    
    # テーブル作成(テーブルない場合)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS stock_price (
        Date TEXT PRIMARY KEY,
        Close REAL,
        Volume REAL
    )
    ''')

    #データ挿入
    for index, row in df.iterrows():
        date_str = index.strftime('%Y-%m-%d')
        cur.execute('''
        INSERT OR IGNORE INTO stock_price (Date, Close, Volume)
        VALUES (?, ?, ?)
        ''', (date_str, row['Close'], row['Volume']))

    conn.commit()
    conn.close()
    
    #データ数確認
    # cur.execute("SELECT COUNT(*) FROM stock_price")
    # total_rows = cur.fetchone()[0]
    # print(f"現在のデータ件数: {total_rows}件")    
    
if __name__ == "__main__":
    update_nintendo_db()