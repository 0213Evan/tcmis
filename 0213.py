import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

keyword = input("請輸入姓名關鍵字 : ")
collection_ref = db.collection("資管二B2026")

docs = collection_ref.get()
for doc in docs:
    teacher = doc.to_dict()
    if keyword in teacher["name"]:
        print(teacher)