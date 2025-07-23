from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import routes

# FastAPI 앱 생성
app = FastAPI(
    title="My FastAPI Project",
    version="1.0.0",
    description="A simple FastAPI example with clean structure.",
)

# CORS 설정 (필요에 따라 origins 수정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 제한해야 함
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(routes.router)

@app.on_event("shutdown")
async def on_shutdown():
    print("Shutting down...")

# uvicorn으로 직접 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
