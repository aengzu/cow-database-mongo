# cow_db

## 사용 방법
### 1. 가상환경 생성
```
python -m venv venv
```

### 2. 가상환경 활성화
```
venv/Scripts/activate
```

### 3. 필요한 패키지 설치
```
pip install -r requirements.txt
```


### 4. 서버 실행
```
uvicorn main:app -reload
```

### 5. 필요시 웹앱 애플리케이션 실행
```
streamlit run app_streamlit.py
```
