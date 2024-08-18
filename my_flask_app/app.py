from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

app = Flask(__name__)

# Google Sheetsの認証情報を設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# シートのデータを取得
spreadsheet_id = 'YOUR_SPREADSHEET_ID'
sh = client.open_by_key(spreadsheet_id)
worksheet = sh.worksheet('シート2')

def fetch_data():
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def plot_graph(df, area):
    plt.figure(figsize=(12, 8))
    df.plot(x='年月', y=['北海道電力', 'A社', 'B社', 'C社'], marker='o')
    plt.title(f'{area}の電気料金推移')
    plt.xlabel('年月')
    plt.ylabel('電気料金（円）')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/graph.png')

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
