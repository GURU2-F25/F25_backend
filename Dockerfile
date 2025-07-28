# 1. 공식 Python 이미지를 기반으로 사용
FROM python:3.9.12

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 앱 전체 복사
COPY . .

# 5. 서버 실행 (Render가 포트 10000에서 감지하므로 반드시 설정)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]