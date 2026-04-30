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
    return link

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