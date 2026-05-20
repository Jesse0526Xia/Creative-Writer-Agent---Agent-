"""FastAPI 应用入口"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

from app.config import settings, BASE_DIR
from app.api.routes import write, character, material, session, project
from app.api.routes import write as write_route
from app.api.routes import character as char_route
from app.api.routes import material as mat_route
from app.api.routes import session as sess_route
from app.api.routes import project as proj_route

# 创建FastAPI应用
app = FastAPI(
    title="Creative Writer Agent",
    description="多Agent协作智能写作系统",
    version="1.0.0",
)


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """自定义 CORS 中间件，确保 preflight 请求正确返回"""
    # 拦截 preflight OPTIONS 请求，直接返回 200 + CORS headers
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "")
        allowed_origins = settings.allowed_origins.split(",") if isinstance(settings.allowed_origins, str) else settings.allowed_origins

        if origin in allowed_origins:
            allow_origin = origin
        elif settings.debug:
            allow_origin = "*"
        else:
            allow_origin = origin

        from fastapi.responses import Response
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            }
        )

    origin = request.headers.get("origin", "")
    allowed_origins = settings.allowed_origins.split(",") if isinstance(settings.allowed_origins, str) else settings.allowed_origins
    if origin in allowed_origins:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With"
        return response
    else:
        if settings.debug:
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With"
            return response
        return await call_next(request)

# 注册路由
app.include_router(proj_route.router, prefix="/api/project", tags=["项目"])
app.include_router(char_route.router, prefix="/api/character", tags=["角色"])
app.include_router(mat_route.router, prefix="/api/material", tags=["素材"])
app.include_router(sess_route.router, prefix="/api/session", tags=["会话"])
app.include_router(write_route.router, prefix="/api", tags=["写作"])

# 挂载静态文件目录
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """首页"""
    return {
        "message": "Creative Writer Agent API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
