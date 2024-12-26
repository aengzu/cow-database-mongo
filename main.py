import requests
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
import base64
from gridfs import GridFS
from bson import ObjectId
from io import BytesIO

from database import collection, fs
from models import CowData

# FastAPI 앱 생성
app = FastAPI(
    title="cow data API"
)


def convert_object_id(data):
    """Recursively convert ObjectId to string in MongoDB documents."""
    if isinstance(data, list):
        return [convert_object_id(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_object_id(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    return data

@app.get("/retrieve_all")
async def retrieve_all_cow_data():
    print('Retrieving all data from MongoDB...')
    data = list(collection.find())
    if not data:
        return []
    return convert_object_id(data)

@app.get("/retrieve/{barcode}")
async def retrieve_cow_data(barcode: str):
    data = collection.find_one({"barcode": barcode})
    if not data:
        raise HTTPException(status_code=404, detail="Data not found.")
    return convert_object_id(data)

@app.get("/test_mongo")
async def test_mongo():
    try:
        data = collection.find_one()
        print(f"Test MongoDB connection: {data}")
        return {"status": "success", "data": convert_object_id(data)}
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="MongoDB connection failed")


@app.get("/retrieve_image/{barcode}")
async def retrieve_image_data(barcode: str):
    try:
        # MongoDB에서 데이터 검색
        data = collection.find_one({"barcode": barcode})
        if not data:
            print(f"No data found for barcode: {barcode}")
            raise HTTPException(status_code=404, detail="Data not found for this barcode.")

        # data 필드 확인
        if "data" not in data or not isinstance(data["data"], list):
            raise HTTPException(status_code=404, detail="No data field found for this barcode.")

        # GridFS 이미지 필터링
        gridfs_image = next((item for item in data["data"] if item.get("type") == "gridfs"), None)
        if not gridfs_image or "file_id" not in gridfs_image:
            print(f"No GridFS image found in data for barcode: {barcode}")
            raise HTTPException(status_code=404, detail="No GridFS image found in data field.")

        file_id = gridfs_image["file_id"]
        print(f"Attempting to fetch GridFS file with ID: {file_id}")

        # GridFS 파일 읽기
        try:
            gridfs_file = fs.get(ObjectId(file_id))
            print(f"File successfully retrieved: {gridfs_file}")
        except Exception as e:
            print(f"Error retrieving GridFS file: {e}")
            raise HTTPException(status_code=404, detail=f"GridFS file not found: {str(e)}")

        return StreamingResponse(BytesIO(gridfs_file.read()), media_type="image/jpeg")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/upload_image_gridfs")
async def upload_image_to_gridfs(barcode: str, image_file: UploadFile):
    # 중복 확인
    if collection.find_one({"barcode": barcode}):
        raise HTTPException(status_code=400, detail="Barcode already exists.")

    # 이미지 저장
    try:
        file_id = fs.put(await image_file.read(), filename=image_file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store image: {str(e)}")

    # 메타데이터와 파일 ID 저장
    document = {
        "barcode": barcode,
        "data": [{
            "type": "gridfs",
            "file_id": str(file_id),
            "description": f"Image for barcode {barcode}"
        }]
    }
    collection.insert_one(document)
    return {"message": "Image uploaded successfully", "barcode": barcode, "file_id": str(file_id)}


@app.get("/stream_image/{file_id}")
async def stream_image(file_id: str):
    try:
        # 디버깅: file_id 확인
        print(f"Fetching file with ID: {file_id}")

        gridfs_file = fs.get(ObjectId(file_id))

        # 디버깅: 파일 정보 출력
        print(f"File retrieved: {gridfs_file}")

        return StreamingResponse(BytesIO(gridfs_file.read()), media_type="image/png")
    except Exception as e:
        print(f"Error retrieving file: {str(e)}")  # 디버깅용 로그
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

