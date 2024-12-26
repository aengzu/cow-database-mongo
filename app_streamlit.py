import streamlit as st
import requests
import pandas as pd

# FastAPI URL
FASTAPI_URL = "http://127.0.0.1:8000"

st.title("🐂 DashBoard")

# 탭 분리
tab1, tab2, tab3, tab4 = st.tabs(["📊 데이터 요약", "🔍 데이터 조회", "➕ 데이터 삽입", "🔤 텍스트로 데이터 삽입"])
# 데이터 요약 탭
with tab1:
    st.header("데이터 요약")
    response = requests.get(f"{FASTAPI_URL}/retrieve_all")
    if response.status_code == 200:
        data = response.json()
        total_barcodes = len(data)
        st.metric("전체 데이터 개수", total_barcodes)

        # 전체 데이터 테이블 표시
        if data:
            df = pd.DataFrame(data)
            # ObjectId 제거 및 중첩 데이터 처리
            if "_id" in df.columns:
                df = df.drop(columns=["_id"])  # _id 필드 제거
            if "meta" in df.columns:
                meta_df = pd.json_normalize(df["meta"])  # meta 필드를 분리
                df = pd.concat([df.drop(columns=["meta"]), meta_df], axis=1)
            if "data" in df.columns:
                df = df.drop(columns=["data"])  # data 필드는 필요에 따라 처리

            st.markdown("### 전체 데이터 테이블")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("표시할 데이터가 없습니다.")
    else:
        st.error("Failed to fetch data for dashboard.")

# 데이터 조회 탭
with tab2:
    st.header("바코드로 데이터 조회")

    col1, col2 = st.columns(2)

    # 드롭다운
    with col1:
        selected_barcode = st.selectbox("바코드 선택", [""] + (df["barcode"].tolist() if 'df' in locals() else []))

    # 검색
    with col2:
        search_barcode = st.text_input("or 바코드 직접 입력")

    # 선택된 바코드 처리
    barcode_to_query = search_barcode or selected_barcode

    if barcode_to_query:
        st.markdown(f"### Details for Barcode: {barcode_to_query}")

        # 데이터 조회
        details_response = requests.get(f"{FASTAPI_URL}/retrieve/{barcode_to_query}")
        if details_response.status_code == 200:
            details = details_response.json()
            # meta 키 확인 후 표시
            if "meta" in details:
                st.json(details["meta"])
            else:
                st.warning("Metadata not available for this barcode.")

            # 이미지 표시
            image_response = requests.get(f"{FASTAPI_URL}/retrieve_image/{barcode_to_query}", stream=True)
            if image_response.status_code == 200:
                st.image(image_response.content, caption=f"Image for Barcode: {barcode_to_query}")
            else:
                st.error(f"Error fetching image: {image_response.status_code} - {image_response.text}")
        else:
            st.error("Failed to fetch metadata for the entered barcode.")
    else:
        st.info("Select a barcode from the dropdown or enter a barcode to search.")

# 데이터 삽입 탭
with tab3:
    st.header("새로운 데이터 삽입")

    barcode = st.text_input("바코드 입력")
    cow_id = st.text_input("소 ID")
    birth_date = st.text_input("출생일 (YYYY-MM-DD 형식)")
    breed = st.text_input("품종")
    weight = st.number_input("무게 (kg)", min_value=0, step=1)
    file = st.file_uploader("이미지 업로드", type=["jpg", "png"])

    if st.button("데이터 삽입", key="insert_button"):  # 고유 키 추가
        if barcode:
            # 데이터 삽입 요청
            try:
                # 업로드된 파일 처리
                image_data = file.read() if file else None  # 파일 내용을 읽음
                response = requests.post(
                    f"{FASTAPI_URL}/upload_image_gridfs",
                    params={"barcode": barcode},  # barcode를 query parameter로 전달
                    data={
                        "cow_id": cow_id or "",
                        "birth_date": birth_date or "",
                        "breed": breed or "",
                        "weight": weight or 0,
                    },
                    files={"image_file": ("uploaded_image.jpg", image_data)} if image_data else None,  # 파일 이름 추가
                )
                if response.status_code == 200:
                    st.success("데이터 삽입 완료!")
                else:
                    st.error(f"삽입 실패: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"삽입 중 오류 발생: {str(e)}")
        else:
            st.warning("바코드를 입력하세요.")


# 텍스트 데이터 삽입 탭
with tab4:
    st.header("새로운 텍스트 데이터 삽입")

    text_content = st.text_area("텍스트 입력", placeholder='''{
    "barcode": "123456789",
    "meta": {
        "timestamp": "2024-12-26T12:00:00Z",
        "cow_id": "COW001",
        "birth_date": "2020-05-15",
        "breed": "Holstein",
        "weight": 450
    },
    "data": []
}.''')

    if st.button("텍스트 삽입", key="text_insert_button"):
        if text_content:
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/insert_json",
                    json={"content": text_content},  # JSON body로 전달
                )
                if response.status_code == 200:
                    st.success("텍스트 데이터 삽입 완료!")
                else:
                    st.error(f"삽입 실패: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"삽입 중 오류 발생: {str(e)}")
        else:
            st.warning("텍스트를 입력하세요.")