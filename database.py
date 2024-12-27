from pymongo import MongoClient
from gridfs import GridFS

# TODO: database 이름, 컬렉션 이름 변경하기
# MongoDB Atlas 연결 설정
MONGO_URI = "localhost:27017"
client = MongoClient(MONGO_URI)
db = client["cow_database"]  # 데이터베이스 이름
collection = db["cow_data"]  # Cow 데이터 컬렉션
fs = GridFS(db)  # GridFS 초기화

