"""
素材管理接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Optional, List
import uuid
from datetime import datetime
from pathlib import Path

from models.schemas import ApiResponse
from app.config import settings

router = APIRouter()


@router.post("/upload", response_model=ApiResponse)
async def upload_material(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    project_id: Optional[str] = None
):
    """上传素材文件"""
    from core.rag import get_material_retriever
    from core.parser import get_document_parser

    try:
        content = await file.read()
        if len(content) > settings.max_material_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件太大，最大支持 {settings.max_material_size // 1024 // 1024}MB"
            )

        parser = get_document_parser()
        text = parser.parse_bytes(content, file.filename)

        if not text:
            raise HTTPException(status_code=400, detail="无法提取文件内容")

        file_ext = Path(file.filename).suffix.lower()
        save_path = Path(settings.material_upload_path)
        save_path.mkdir(parents=True, exist_ok=True)

        saved_file = save_path / f"{uuid.uuid4()}{file_ext}"
        with open(saved_file, "wb") as f:
            f.write(content)

        retriever = get_material_retriever()
        material_id = retriever.add_material(
            content=text,
            file_name=file.filename,
            file_type=file_ext,
            metadata={
                "description": description,
                "saved_path": str(saved_file),
                "size": len(content)
            },
            project_id=project_id
        )

        return ApiResponse(
            success=True,
            message="素材上传成功",
            data={
                "id": material_id,
                "file_name": file.filename,
                "content_preview": text[:500],
                "content_length": len(text)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/text", response_model=ApiResponse)
async def upload_text_material(
    content: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    project_id: Optional[str] = None
):
    """上传纯文本素材"""
    from core.rag import get_material_retriever

    try:
        if not content or len(content) < 10:
            raise HTTPException(status_code=400, detail="内容太少")

        retriever = get_material_retriever()
        material_id = retriever.add_material(
            content=content,
            file_name=name or "text_material",
            file_type=".txt",
            metadata={"description": description},
            project_id=project_id
        )

        return ApiResponse(
            success=True,
            message="素材添加成功",
            data={
                "id": material_id,
                "content_preview": content[:500],
                "content_length": len(content)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=ApiResponse)
async def search_materials(
    query: str = Query(..., description="搜索关键词"),
    k: int = Query(5, ge=1, le=20, description="返回数量"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    project_id: Optional[str] = Query(None, description="项目ID过滤")
):
    """搜索相似素材"""
    from core.rag import get_material_retriever

    try:
        retriever = get_material_retriever()
        results = retriever.search(query, k=k, file_type=file_type, project_id=project_id)

        return ApiResponse(
            success=True,
            data={
                "query": query,
                "count": len(results),
                "results": results
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{material_id}", response_model=ApiResponse)
async def get_material(material_id: int):
    """获取素材详情"""
    from core.rag import get_material_retriever

    retriever = get_material_retriever()
    material = retriever.get_material(material_id)

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    return ApiResponse(
        success=True,
        data=material
    )


@router.delete("/{material_id}", response_model=ApiResponse)
async def delete_material(material_id: int):
    """删除素材"""
    from core.rag import get_material_retriever

    retriever = get_material_retriever()
    retriever.delete_material(material_id)

    return ApiResponse(
        success=True,
        message="素材删除成功"
    )
