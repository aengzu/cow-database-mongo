from pymongo import MongoClient
from gridfs import GridFS

# MongoDB Atlas 연결 설정
MONGO_URI = "mongodb+srv://wjsdudwn01:rhaxod0820@cluster0.18uzq.mongodb.net/cow_database?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["cow_database"]  # 데이터베이스 이름
collection = db["cow_data"]  # Cow 데이터 컬렉션
fs = GridFS(db)  # GridFS 초기화

