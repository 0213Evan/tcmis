import requests
from bs4 import BeautifulSoup
url = "https://www1.pu.edu.tw/~tcyang/course.html"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("a")

for i in result:
	print(i.text, i.get("href"))
	print()