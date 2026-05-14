import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template,request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入賴期騰的網站20260326</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=期騰&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字:賴)</a><hr>"
    link += "<a href=/spider1>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    link += "<a href=/spiderMovie>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/searchMovie>從資料庫搜尋電影關鍵字</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/weather>查詢縣市天氣與降雨機率</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"

    return link

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=["GET", "POST"])
def weather():
    import urllib3
    # 關閉 SSL 憑證警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 1. 建立前端介面 (標題與輸入表單)
    R = "<h1>縣市天氣與降雨機率查詢</h1>"
    R += "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST' action='/weather'>"
    R += "請輸入欲查詢的縣市: <input type='text' name='city' placeholder='例如:臺中市' required>"
    R += "<button type='submit'>查詢</button>"
    R += "</form><hr>"

    # 2. 當使用者按下「查詢」送出資料時 (POST)
    if request.method == "POST":
        # 取得表單輸入的縣市，並將「台」替換為「臺」防呆
        city = request.form.get("city", "")
        city_formatted = city.replace("台", "臺")

        # 設定 API 網址與偽裝瀏覽器的 headers
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&format=JSON&locationName=" + city_formatted
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            # 發送請求並解析 JSON
            Data = requests.get(url, headers=headers, verify=False)
            JsonData = json.loads(Data.text)
            locations = JsonData["records"]["location"]

            # 檢查是否有抓到資料
            if len(locations) > 0:
                loc_data = locations[0]
                
                # 抓取天氣現象與降雨機率
                Weather = loc_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                Rain = loc_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
                
                # 將結果組合成 HTML 顯示在畫面上
                R += f"<h2>查詢結果：</h2>"
                R += f"<h3>{loc_data['locationName']} 目前天氣：{Weather}，降雨機率 {Rain}%</h3>"
            else:
                R += f"<h3 style='color:red;'>找不到「{city}」的資料，請確認是否輸入了完整的縣市名稱（例如：臺中市）。</h3>"
                
        except Exception as e:
            R += f"<h3>發生錯誤：{str(e)}</h3>"

    return R

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者:期騰</h1><br>"

    import requests, json

    url = " https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url, verify=False)
    #print(Data.text)
    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",原因:" + item["主要肇因"] + ",件數:" + item["總件數"] + "<br>"
        
    return R

@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    db = firestore.client()
    collection_ref = db.collection("電影2B")
    
    R = "<h1>查詢資料庫電影</h1>"
    R += "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST' action='/searchMovie'>"
    R += "請輸入電影名稱關鍵字: <input type='text' name='keyword'>"
    R += "<button type='submit'>搜尋</button>"
    R += "</form><hr>"

    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        docs = collection_ref.get()
        
        found = False
        count = 0
        for doc in docs:
            movie = doc.to_dict()
            title = movie.get("title", "")
            
            # 進行關鍵字比對
            if keyword in title:
                found = True
                count += 1
                # 顯示資訊：編號(doc.id)、片名、海報、介紹頁連結、上映日期
                R += f"<h3>編號：{doc.id}</h3>"
                R += f"<b>片名：{title}</b><br>"
                R += f"上映日期：{movie.get('showDate')}<br>"
                R += f"<a href='{movie.get('hyperlink')}' target='_blank'>查看電影介紹</a><br>"
                R += f"<img src='{movie.get('picture')}' width='200'><br><hr>"
        
        if not found:
            R += f"<h3>很抱歉，資料庫中找不到包含「{keyword}」的電影。</h3>"
        else:
            R += f"共找到 {count} 部相關電影。"

    return R

@app.route("/spiderMovie")
def spiderMovie():
    R = ""

    db = firestore.client()


    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間:", "")
    result=sp.select(".filmListAllX li")
    #info = ""
    total = 0
    for item in result:
        total += 1
        movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
        title = item.find(class_="filmtitle").text
        picture = "https://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "https://www.atmovies.com.tw" + item.find("a").get("href")

        showDate = item.find(class_="runtime").text[5:15]
        #info += movie_id + "\n" + title + "\n"
        #info += picture + "\n" + hyperlink + "\n" + showDate + "\n\n"


        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影2B").document(movie_id)
        doc_ref.set(doc)

    R += "網站最近更新日期:" + lastUpdate + "<br>" + "總共爬取" + str(total) + "部電影到資料庫"

    return R


@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    # 1. 建立標題、返回首頁連結與搜尋表單
    R = "<h1>近期上映電影</h1>"
    R += "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST' action='/movie1'>"
    R += "請輸入電影名稱: <input type='text' name='keyword'>"
    R += "<button type='submit'>搜尋</button>"
    R += "</form><hr>"

    # 2. 接收使用者輸入的關鍵字 (修正縮排)
    keyword = ""
    if request.method == "POST":
        keyword = request.form.get("keyword", "")

    # 3. 進行網頁爬蟲
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    found = False 

    # 4. 處理爬取到的資料並進行比對 (修正縮排)
    for item in result:
        a_tag = item.find("a")
        img_tag = item.find("img")

        if a_tag and img_tag:
            movie_title = img_tag.get("alt")

            # 如果沒有輸入關鍵字就顯示全部，如果有就進行包含比對
            if not keyword or (keyword in movie_title):
                found = True
                L = "https://www.atmovies.com.tw" + a_tag.get("href") # 修正網址路徑
                R += "<a href=" + L + ">" + movie_title + "</a><br>"
                post = img_tag.get("src")
                # 處理可能的相對路徑
                if not post.startswith("http"):
                    post = "https://www.atmovies.com.tw" + post
                R += "<img src=" + post + " width='200'></img><br><br>"

    # 5. 如果搜尋了但沒找到任何結果
    if keyword and not found:
        R += f"<h3>找不到包含「{keyword}」的電影喔！</h3>"

    return R

@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")
    
    for i in result:
        R += i.text + i.get("href") + "<br>"
    return R

@app.route("/read2", methods=["GET", "POST"])
def read2():
    db = firestore.client()
    collection_ref = db.collection("資管二B2026")
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        docs = collection_ref.get()
        
        result_list = []
        for doc in docs:
            teacher = doc.to_dict()
            teacher_name = teacher.get("name", "")
            if keyword in teacher_name:
                result_list.append(teacher)
        
        return render_template("search.html", keyword=keyword, result=result_list)
    
    return render_template("search.html")
@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("資管二B2026")    
    docs = collection_ref.get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"
    return Result


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    now = datetime.now()
    return render_template("about.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep = d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            y = float(request.form["y"])
            opt = request.form["opt"]
           
            if opt == "pow":

                result = x ** y
                msg = f"{x} 的 {y} 次方 = {result}"
            elif opt == "root":

                if x < 0 and y % 2 == 0:
                    msg = "錯誤：負數不能開偶數次方根"
                else:
                    result = x ** (1/y)
                    msg = f"{x} 的 {y} 次方根 = {result}"
            else:
                msg = "無效的運算"
        except Exception as e:
            msg = f"計算出錯：{str(e)}"
           
        return f"<h1>計算結果</h1><p>{msg}</p><a href='/math'>重新計算</a>"

    return render_template("math.html")
if __name__ == "__main__":
    app.run(debug=True)