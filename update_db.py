import sqlite3
import yfinance as yf
import pandas as pd
from config import TICKERS, DB_PATH

def update_stock_db():
    #DB接続（with文で安全にクローズ）
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # テーブル構造の確認とマイグレーション
        try:
            cur.execute("PRAGMA table_info(stock_price)")
            columns = [info[1] for info in cur.fetchall()]
            
            # Tickerカラムがない場合（旧スキーマ）の移行処理
            # テーブルが存在して、かつTickerがない場合のみ実行
            if columns and 'Ticker' not in columns:
                print("旧スキーマを検出しました。マイグレーションを実行します...")
                cur.execute("ALTER TABLE stock_price RENAME TO stock_price_old")
                
                # 新テーブル作成
                cur.execute('''
                CREATE TABLE stock_price (
                    Date TEXT,
                    Ticker TEXT,
                    Close REAL,
                    Volume REAL,
                    PRIMARY KEY (Date, Ticker)
                )
                ''')
                
                # データの移行（既存データは全て任天堂として扱う）
                cur.execute('''
                INSERT INTO stock_price (Date, Ticker, Close, Volume)
                SELECT Date, '7974.T', Close, Volume FROM stock_price_old
                ''')
                
                cur.execute("DROP TABLE stock_price_old")
                print("マイグレーション完了")

        except sqlite3.OperationalError:
            # テーブルが存在しない場合は何もしない
            pass
        
        # テーブル作成(テーブルない場合)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS stock_price (
            Date TEXT,
            Ticker TEXT,
            Close REAL,
            Volume REAL,
            PRIMARY KEY (Date, Ticker)
        )
        ''')

        for ticker in TICKERS:
            print(f"{TICKERS[ticker]}({ticker})のデータを取得中...")
            #株価取得
            try:
                df = yf.Ticker(ticker).history(period="5d")[['Close', 'Volume']]
                if df.empty:
                    print(f"{ticker}: データが取得できませんでした")
                    continue
                    
                df.index.name = 'Date'

                #データ挿入
                for index, row in df.iterrows():
                    date_str = index.strftime('%Y-%m-%d')
                    cur.execute('''
                    INSERT OR IGNORE INTO stock_price (Date, Ticker, Close, Volume)
                    VALUES (?, ?, ?, ?)
                    ''', (date_str, ticker, row['Close'], row['Volume']))
            except Exception as e:
                print(f"{ticker}の取得中にエラーが発生しました: {e}")
        
        conn.commit()
        
        #データ数確認
        cur.execute("SELECT Ticker, COUNT(*) FROM stock_price GROUP BY Ticker")
        rows = cur.fetchall()
        print("現在のデータ件数:")
        for row in rows:
            print(f"{row[0]}: {row[1]}件")
    
if __name__ == "__main__":
    update_stock_db()