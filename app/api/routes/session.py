"""
会话管理接口
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List

from models.schemas import ApiResponse, SessionStatus, RevisionRequest
from app.api.routes.write import _sessions

router = APIRouter()


@router.get("/{session_id}", response_model=ApiResponse)
async def get_session(session_id: str):
    """获取会话详情"""
    session = _sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ApiResponse(
        success=True,
        data=session
    )


@router.get("/{session_id}/versions", response_model=ApiResponse)
async def get_session_versions(session_id: str):
    """获取版本历史"""
    session = _sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 简单的版本历史（实际应从数据库获取）
    versions = session.get("versions", [])

    return ApiResponse(
        success=True,
        data={
            "session_id": session_id,
            "current_version": session.get("current_version", 1),
            "versions": versions
        }
    )


@router.post("/{session_id}/revise", response_model=ApiResponse)
async def revise_session(session_id: str, request: RevisionRequest):
    """
    发送修改指令

    这会触发新一轮的迭代修改
    """
    session = _sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="只能在完成状态下进行修改"
        )

    # 添加修改指令到队列
    if "revision_queue" not in session:
        session["revision_queue"] = []
    session["revision_queue"].append({
        "instruction": request.instruction,
        "target_section": request.target_section
    })

    return ApiResponse(
        success=True,
        message="修改指令已添加",
        data={
            "queue_length": len(session["revision_queue"])
        }
    )


@router.delete("/{session_id}", response_model=ApiResponse)
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in _sessions:
        del _sessions[session_id]

    return ApiResponse(
        success=True,
        message="会话删除成功"
    )
