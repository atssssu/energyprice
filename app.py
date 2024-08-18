from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import pandas as pd
import japanize_matplotlib
from google.colab import auth
from google.auth import default
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import ipywidgets as widgets
from IPython.display import display


app = Flask(__name__)


# 日本語フォントを使用するための設定
japanize_matplotlib.japanize()

# Google 認証
auth.authenticate_user()

# google-auth の認証情報を取得
creds, _ = default()

# gspread の認証
gc = gspread.authorize(creds)

# スプレッドシートのIDを指定して開く
spreadsheet_id = '112eANC8wPOkdcUjB5rvIIag6LXtjI9dQJ4ByCoaWCt4'
sh = gc.open_by_key(spreadsheet_id)

# シートを名前で指定
worksheet = sh.worksheet('Sheet4')

# Google Sheetsのデータを取得
data = worksheet.get_all_values()

# Pandas DataFrameに変換
df = pd.DataFrame(data[1:], columns=data[0])  # 最初の行をヘッダーとして使用

# 設定
契約電力 = 270  # 契約電力
使用量 = 600000  # 使用量

def calculate_total_price(df, companies, area_prefix, 契約電力, 使用量):
    result = pd.DataFrame(index=df.index)  # 新しい列を保存するための一時的なDataFrame

    for company_name in companies:
        try:
            # カンマを削除し、小数点を含む数値データに変換
            df[f'{area_prefix}{company_name}_基本料金'] = pd.to_numeric(df[f'{area_prefix}{company_name}_基本料金'].str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)
            df[f'{area_prefix}{company_name}_使用料金_kaki'] = pd.to_numeric(df[f'{area_prefix}{company_name}_使用料金_kaki'].str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)
            df[f'{area_prefix}{company_name}_使用料金_taki'] = pd.to_numeric(df[f'{area_prefix}{company_name}_使用料金_taki'].str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)
            df[f'{area_prefix}{company_name}_燃料調整費'] = pd.to_numeric(df[f'{area_prefix}{company_name}_燃料調整費'].str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)

            # 電気料金総額を計算
            result[f'{area_prefix}{company_name}_総価格'] = (
                契約電力 * df[f'{area_prefix}{company_name}_基本料金'] +
                使用量 * df[f'{area_prefix}{company_name}_使用料金_kaki'] +
                使用量 * df[f'{area_prefix}{company_name}_使用料金_taki'] +
                使用量 * df[f'{area_prefix}{company_name}_燃料調整費']
            ).round(0)  # 小数点以下を四捨五入

            # メッセージ出力をコメントアウト
            # print(f"{area_prefix}{company_name}_総価格 列の生成成功")
        except KeyError as e:
            print(f"Error processing data for {area_prefix}{company_name}: {e}")
        except Exception as e:
            print(f"Unexpected error processing data for {area_prefix}{company_name}: {e}")

    # 計算結果を元のDataFrameに結合
    df = pd.concat([df, result], axis=1)
    return df

    
# エリアごとの会社名とプレフィックスを定義
areas = {
    "北海道エリア": {
        "prefix": "hokkaido_",
        "companies": ['北海道電力', 'A社', 'B社', 'C社']
    },
    "東北エリア": {
        "prefix": "tohoku_",
        "companies": ['東北電力', 'A社', 'B社', 'C社']
    },
    "北陸エリア": {
        "prefix": "hokuriku_",
        "companies": ['北陸電力', 'A社', 'B社', 'C社']
    },
    "東京エリア": {
        "prefix": "tokyo_",
        "companies": ['東京電力', 'A社', 'B社', 'C社']
    },
    "中部エリア": {
        "prefix": "chubu_",
        "companies": ['中部電力', 'A社', 'B社', 'C社']
    },
    "関西エリア": {
        "prefix": "kansai_",
        "companies": ['関西電力', 'A社', 'B社', 'C社']
    },
    "中国エリア": {
        "prefix": "chugoku_",
        "companies": ['中国電力', 'A社', 'B社', 'C社']
    },
    "四国エリア": {
        "prefix": "shikoku_",
        "companies": ['四国電力', 'A社', 'B社', 'C社']
    },
    "九州エリア": {
        "prefix": "kyushu_",
        "companies": ['九州電力', 'A社', 'B社', 'C社']
    }
}

# 会社データの計算を行う
for area, details in areas.items():
    area_prefix = details["prefix"]
    companies = details["companies"]
    df = calculate_total_price(df, companies, area_prefix, 契約電力, 使用量)

# エリア選択のプルダウンメニューを作成
area_dropdown = widgets.Dropdown(
    options=list(areas.keys()),
    value='北海道エリア',
    description='利用エリア:',
)

# 折れ線グラフを描画する関数
def plot_graph(area):
    details = areas[area]
    area_prefix = details["prefix"]
    companies = details["companies"]

    # データが存在する会社のみを対象にする
    available_companies = [company for company in companies if f'{area_prefix}{company}_総価格' in df.columns and not df[f'{area_prefix}{company}_総価格'].isnull().all()]

    if available_companies:  # データがある会社が存在する場合のみプロット
        # グラフの描画
        plt.figure(figsize=(12, 8))
        line_styles = ['-', '--', '-.', ':']
        markers = ['o', 'v', '^', 's']

        for i, company in enumerate(available_companies):
            # データが空白（NaN）の場合、その会社のデータをプロットしない
            if not df[f'{area_prefix}{company}_総価格'].isnull().all():
                plt.plot(df['年月'], df[f'{area_prefix}{company}_総価格'], label=company, linestyle=line_styles[i], marker=markers[i])

        # y軸の範囲を狭める
        min_y = df[[f'{area_prefix}{company}_総価格' for company in available_companies]].min().min()
        max_y = df[[f'{area_prefix}{company}_総価格' for company in available_companies]].max().max()
        plt.ylim(min_y - (max_y - min_y) * 0.05, max_y + (max_y - min_y) * 0.05)  # y軸に余裕を持たせつつ狭める

        plt.title(f'{area}の電力会社の電気料金推移', fontsize=16)
        plt.xlabel('年月', fontsize=14)
        plt.ylabel('電気料金（円）', fontsize=14, rotation=0, labelpad=40)  # ラベルを横に表示
        plt.gca().yaxis.set_ticks([])  # y軸の目盛を消去
        plt.xticks(rotation=60)
        plt.grid(True)
        plt.legend(fontsize=12)
        plt.tight_layout()  # グラフのレイアウトを調整
        plt.show()
    else:
        print(f"{area}には利用可能なデータがありません。")

# 選択されたエリアに応じてグラフを更新
widgets.interact(plot_graph, area=area_dropdown);





@app.route('/')
def index():
    df = fetch_data()
    plot_graph(df, '北海道エリア')
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        details = request.form['details']
        # ここでフォームデータを処理する（データベースに保存、メール送信など）
        return f'送信されました: {name}, {email}, {phone}, {details}'
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
