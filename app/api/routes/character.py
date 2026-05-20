"""
角色管理接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, List
import uuid
from datetime import datetime

from models.schemas import ApiResponse, CharacterCreateRequest, CharacterProfile

router = APIRouter()


@router.post("/create", response_model=ApiResponse)
async def create_character(request: CharacterCreateRequest):
    """创建角色"""
    from core.character import get_character_manager

    try:
        manager = get_character_manager()

        profile = manager.create_character(
            name=request.name,
            gender=request.gender,
            age=request.age,
            occupation=request.occupation,
            personality_traits=request.personality_traits,
            mbti=request.mbti,
            speaking_style=request.speaking_style,
            catchphrases=request.catchphrases,
            background=request.background,
            relationships=request.relationships,
            custom_fields=request.custom_template,
            project_id=request.project_id
        )

        return ApiResponse(
            success=True,
            message="角色创建成功",
            data=profile.model_dump()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{char_id}", response_model=ApiResponse)
async def get_character(char_id: str):
    """获取角色"""
    from core.character import get_character_manager

    manager = get_character_manager()
    profile = manager.get_character(char_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Character not found")

    return ApiResponse(
        success=True,
        data=profile.model_dump()
    )


@router.get("/", response_model=ApiResponse)
async def list_characters(project_id: Optional[str] = None):
    """列出角色"""
    from core.character import get_character_manager

    manager = get_character_manager()
    profiles = manager.list_characters(project_id=project_id)

    return ApiResponse(
        success=True,
        data=[p.model_dump() for p in profiles]
    )


@router.put("/{char_id}", response_model=ApiResponse)
async def update_character(char_id: str, request: CharacterCreateRequest):
    """更新角色"""
    from core.character import get_character_manager

    manager = get_character_manager()

    profile = manager.update_character(
        char_id,
        name=request.name,
        age=request.age,
        occupation=request.occupation,
        personality_traits=request.personality_traits,
        mbti=request.mbti,
        speaking_style=request.speaking_style,
        catchphrases=request.catchphrases,
        background=request.background
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Character not found")

    return ApiResponse(
        success=True,
        message="角色更新成功",
        data=profile.model_dump()
    )


@router.delete("/{char_id}", response_model=ApiResponse)
async def delete_character(char_id: str):
    """删除角色"""
    from core.character import get_character_manager

    manager = get_character_manager()

    if not manager.delete_character(char_id):
        raise HTTPException(status_code=404, detail="Character not found")

    return ApiResponse(
        success=True,
        message="角色删除成功"
    )


@router.post("/from-document", response_model=ApiResponse)
async def extract_from_document(
    file: UploadFile = File(...),
    auto_create: bool = True
):
    """从文档提取角色"""
    from core.parser import get_document_parser
    from core.character import get_character_manager, get_character_analyzer

    try:
        content = await file.read()

        parser = get_document_parser()
        text = parser.parse_bytes(content, file.filename)

        if not text or len(text) < 100:
            raise HTTPException(status_code=400, detail="文档内容太少，无法提取角色")

        analyzer = get_character_analyzer()
        result = analyzer.extract_from_document(text, file.filename)

        created_characters = []
        if auto_create and result.get("characters"):
            manager = get_character_manager()
            for char_data in result["characters"]:
                profile = manager.create_character(
                    name=char_data["name"],
                    age=char_data.get("age"),
                    occupation=char_data.get("occupation"),
                    personality_traits=char_data.get("personality_traits", []),
                    mbti=char_data.get("mbti"),
                    speaking_style=char_data.get("speaking_style"),
                    catchphrases=char_data.get("catchphrases", []),
                    background=char_data.get("background"),
                    custom_fields=char_data.get("custom_fields", {})
                )
                created_characters.append(profile.model_dump())

        return ApiResponse(
            success=True,
            message=f"成功提取 {len(result.get('characters', []))} 个角色",
            data={
                "extracted_count": len(result.get("characters", [])),
                "writing_style": result.get("writing_style"),
                "themes": result.get("themes"),
                "characters": created_characters,
                "raw_result": result
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{char_id}/relationship", response_model=ApiResponse)
async def add_relationship(
    char_id: str,
    related_name: str,
    relation_type: str,
    description: str
):
    """添加人物关系"""
    from core.character import get_character_manager

    manager = get_character_manager()

    if not manager.add_relationship(char_id, related_name, relation_type, description):
        raise HTTPException(status_code=404, detail="Character not found")

    profile = manager.get_character(char_id)

    return ApiResponse(
        success=True,
        message="关系添加成功",
        data=profile.model_dump()
    )


@router.get("/search/similar", response_model=ApiResponse)
async def search_similar(query: str, k: int = 3):
    """搜索相似角色"""
    from core.character import get_character_manager

    manager = get_character_manager()
    profiles = manager.search_similar(query, k=k)

    return ApiResponse(
        success=True,
        data=[p.model_dump() for p in profiles]
    )
