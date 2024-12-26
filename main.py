import requests
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from bson import ObjectId
from io import BytesIO
from database import collection, fs
from models import CowData, MetaData, TextData

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

    # 디버깅: MongoDB 데이터 출력
    print("Retrieved data from MongoDB:", data)

    data = convert_object_id(data)
    data.setdefault("meta", {"message": "No metadata available"})
    return data


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


@app.delete("/delete/{barcode}")
async def delete_cow_data(barcode: str):
    """바코드 ID로 데이터를 삭제."""
    try:
        result = collection.delete_one({"barcode": barcode})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"No data found with barcode {barcode}")
        return {"message": f"Data with barcode {barcode} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete data: {str(e)}")


@app.post("/upload_image_gridfs")
async def upload_image_to_gridfs(
    barcode: str,
    cow_id: str = Form(None),  # 선택적으로 처리
    birth_date: str = Form(None),
    breed: str = Form(None),
    weight: int = Form(None),
    image_file: UploadFile = None
):
    # 중복 확인
    if collection.find_one({"barcode": barcode}):
        raise HTTPException(status_code=400, detail="Barcode already exists.")

    # 이미지 저장
    file_id = None
    if image_file:
        try:
            file_id = fs.put(await image_file.read(), filename=image_file.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store image: {str(e)}")

    # 현재 시각으로 타임스탬프 추가
    from datetime import datetime
    timestamp = datetime.now().isoformat()

    # 메타데이터와 파일 ID 저장
    document = {
        "barcode": barcode,
        "meta": {
            "cow_id": cow_id or "Unknown",  # 기본값 처리
            "birth_date": birth_date or "Unknown",
            "breed": breed or "Unknown",
            "weight": weight or 0,
            "timestamp": timestamp,
        },
        "data": [  # 이미지 데이터 추가
            {
                "type": "gridfs",
                "file_id": str(file_id),
                "description": f"Image for barcode {barcode}"
            }
        ] if file_id else []
    }
    collection.insert_one(document)
    return {"message": "Data inserted successfully", "barcode": barcode, "file_id": str(file_id) if file_id else None}


@app.post("/insert_json")
async def insert_json(data: dict):
    """JSON 데이터를 파싱하여 MongoDB에 저장"""
    try:
        # 데이터를 MongoDB에 삽입
        result = collection.insert_one(data)
        inserted_document = collection.find_one({"_id": result.inserted_id})
        return {"message": "Data inserted successfully", "document": convert_object_id(inserted_document)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert data: {str(e)}")


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

