import streamlit as st
import requests

# FastAPI URL
FASTAPI_URL = "http://127.0.0.1:8000"

st.title("Cow Data Viewer")

# 바코드 리스트 조회
st.header("Barcodes")
response = requests.get(f"{FASTAPI_URL}/retrieve_all")
if response.status_code == 200:
    data = response.json()
    barcodes = [item["barcode"] for item in data]
    selected_barcode = st.selectbox("Select a Barcode", barcodes)
else:
    st.error("Failed to fetch data.")
    selected_barcode = None

# 선택된 바코드 데이터 조회
if selected_barcode:
    st.header(f"Details for Barcode: {selected_barcode}")

    # 데이터 조회
    details_response = requests.get(f"{FASTAPI_URL}/retrieve/{selected_barcode}")
    if details_response.status_code == 200:
        details = details_response.json()
        st.json(details["meta"])
    else:
        st.error("Failed to fetch metadata.")

    # 이미지 표시
    image_response = requests.get(f"{FASTAPI_URL}/retrieve_image/{selected_barcode}")
    if image_response.status_code == 200:
        try:
            image_data = image_response.json()
            if "error" in image_data:
                st.warning(image_data["error"])
            elif image_data["gridfs_image"] and image_data["gridfs_image"]["content"]:
                st.image(image_data["gridfs_image"]["content"], caption=f"Image for Barcode: {selected_barcode}")
            else:
                st.warning("No image available for this barcode.")
        except requests.exceptions.JSONDecodeError:
            st.error("Invalid response from server.")
    else:
        st.error(f"Error: {image_response.status_code} - {image_response.text}")

