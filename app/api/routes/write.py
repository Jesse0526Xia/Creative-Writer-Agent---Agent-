"""
写作接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime

from models.schemas import WriteRequest, WriteResponse, ApiResponse, WritingOutline
from models.schemas import SessionStatus, TaskType, WritingStyle

router = APIRouter()


# 简单的内存存储（生产环境应使用数据库）
_sessions = {}


async def run_writing_workflow(session_id: str):
    """后台运行写作工作流"""
    from core.agents import AgentContext, create_coordinator
    from core.character import get_character_manager
    from core.rag import get_material_retriever

    session = _sessions.get(session_id)
    if not session:
        return

    try:
        char_manager = get_character_manager()
        characters = []
        for char_id in session.get("character_ids", []):
            char = char_manager.get_character(char_id)
            if char:
                characters.append(char.model_dump())

        material_retriever = get_material_retriever()
        materials = []
        for mat_id in session.get("material_ids", []):
            mat = material_retriever.get_material(int(mat_id))
            if mat:
                materials.append(mat)

        context = AgentContext(
            session_id=session_id,
            task_type=session.get("task_type"),
            topic=session.get("topic"),
            style=session.get("style"),
            characters=characters,
            materials=materials,
            outline=session.get("outline"),
            iteration=0
        )

        coordinator = create_coordinator()
        result = coordinator.run_full_workflow(
            context,
            max_iterations=session.get("iterations", 3)
        )

        _sessions[session_id].update({
            "status": "completed" if result.get("status") == "completed" else "failed",
            "final_content": result.get("content"),
            "outline": result.get("outline"),
            "iterations_completed": result.get("iterations", 0),
            "updated_at": datetime.now().isoformat()
        })

    except Exception as e:
        _sessions[session_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })


@router.post("/write", response_model=ApiResponse)
async def write(
    request: WriteRequest,
    background_tasks: BackgroundTasks
):
    """创建写作任务"""
    session_id = str(uuid.uuid4())

    session = {
        "id": session_id,
        "project_id": request.project_id,
        "task_type": request.task_type,
        "topic": request.topic,
        "style": request.style,
        "character_ids": request.character_ids,
        "material_ids": request.material_ids,
        "custom_outline": request.custom_outline,
        "iterations": request.iterations,
        "outline": None,
        "final_content": None,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    _sessions[session_id] = session
    background_tasks.add_task(run_writing_workflow, session_id)

    return ApiResponse(
        success=True,
        message="写作任务已创建",
        data={
            "session_id": session_id,
            "status": "pending"
        }
    )


@router.post("/write/sync", response_model=ApiResponse)
async def write_sync(request: WriteRequest):
    """同步写作接口"""
    from core.agents import AgentContext, create_coordinator
    from core.character import get_character_manager
    from core.rag import get_material_retriever

    session_id = str(uuid.uuid4())

    try:
        char_manager = get_character_manager()
        characters = []
        for char_id in request.character_ids:
            char = char_manager.get_character(char_id)
            if char:
                characters.append(char.model_dump())

        material_retriever = get_material_retriever()
        materials = []
        for mat_id in request.material_ids:
            mat = material_retriever.get_material(int(mat_id))
            if mat:
                materials.append(mat)

        context = AgentContext(
            session_id=session_id,
            task_type=request.task_type.value if isinstance(request.task_type, TaskType) else request.task_type,
            topic=request.topic,
            style=request.style.value if isinstance(request.style, WritingStyle) else request.style,
            characters=characters,
            materials=materials,
            iteration=0
        )

        coordinator = create_coordinator()
        result = coordinator.run_full_workflow(
            context,
            max_iterations=request.iterations
        )

        return ApiResponse(
            success=True,
            message="写作完成",
            data={
                "session_id": session_id,
                "outline": result.get("outline"),
                "content": result.get("content"),
                "iterations": result.get("iterations"),
                "final_score": result.get("final_score")
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/write/status/{session_id}", response_model=ApiResponse)
async def get_write_status(session_id: str):
    """获取写作状态"""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ApiResponse(
        success=True,
        data={
            "session_id": session_id,
            "status": session.get("status"),
            "progress": session.get("progress"),
            "outline": session.get("outline"),
            "content": session.get("final_content"),
            "iterations_completed": session.get("iterations_completed", 0)
        }
    )


@router.get("/config/status", response_model=ApiResponse)
async def get_config_status():
    """获取LLM配置状态"""
    from app.config import settings
    active = settings.active_llm
    key_map = {
        "doubao": settings.doubao_api_key,
        "kimi": settings.kimi_api_key,
        "deepseek": settings.deepseek_api_key
    }
    api_key_configured = bool(key_map.get(active))
    model = getattr(settings, f"{active}_model", "unknown")
    return ApiResponse(
        success=True,
        data={
            "active_llm": active,
            "api_key_configured": api_key_configured,
            "model": model
        }
    )
