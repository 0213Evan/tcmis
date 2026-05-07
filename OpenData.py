import requests, json

url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"

Data = requests.get(url, verify=False)

#print(Data.text)

JsonData = json.loads(Data.text)
for item in JsonData:
	print(item["路口名稱"] + ",原因:",item["主要肇因"])
	print()