"""
项目管理接口
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import uuid
from datetime import datetime

from models.database import Project, Character, Material, Session, Base, SessionLocal, engine
from models.schemas import (
    ApiResponse,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectDetailResponse,
    CharacterProfile
)

router = APIRouter()


def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """确保数据库表存在"""
    Base.metadata.create_all(bind=engine)


@router.post("/create", response_model=ApiResponse)
async def create_project(request: ProjectCreateRequest, db=Depends(get_db)):
    """创建项目"""
    try:
        init_db()
        
        project = Project(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        return ApiResponse(
            success=True,
            message="项目创建成功",
            data={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ApiResponse)
async def list_projects(db=Depends(get_db)):
    """列出所有项目"""
    try:
        init_db()
        
        projects = db.query(Project).order_by(Project.updated_at.desc()).all()
        
        result = []
        for p in projects:
            # 统计项目下的资源数量
            char_count = db.query(Character).filter(Character.project_id == p.id).count()
            mat_count = db.query(Material).filter(Material.project_id == p.id).count()
            sess_count = db.query(Session).filter(Session.project_id == p.id).count()
            
            result.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
                "character_count": char_count,
                "material_count": mat_count,
                "session_count": sess_count
            })

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ApiResponse)
async def get_project(project_id: str, db=Depends(get_db)):
    """获取项目详情"""
    try:
        init_db()
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取项目下的角色
        characters = db.query(Character).filter(Character.project_id == project_id).all()
        char_profiles = []
        for c in characters:
            try:
                profile_data = c.profile_data if isinstance(c.profile_data, dict) else {}
                char_profiles.append({
                    "id": c.id,
                    "name": c.name,
                    "basic": profile_data.get("basic", {}),
                    "personality": profile_data.get("personality", {}),
                    "appearance": profile_data.get("appearance", {}),
                    "speaking": profile_data.get("speaking", {}),
                    "background": profile_data.get("background", {}),
                    "relationships": profile_data.get("relationships", {}),
                    "custom_fields": profile_data.get("custom_fields", {}),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                })
            except:
                char_profiles.append({"id": c.id, "name": c.name})

        # 获取项目下的素材
        materials = db.query(Material).filter(Material.project_id == project_id).all()
        mat_list = []
        for m in materials:
            mat_list.append({
                "id": m.id,
                "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
                "file_name": m.file_name,
                "file_type": m.file_type,
                "metadata": m.meta_info or {},
                "created_at": m.created_at.isoformat() if m.created_at else None
            })

        # 获取项目下的会话
        sessions = db.query(Session).filter(Session.project_id == project_id).order_by(Session.created_at.desc()).all()
        sess_list = []
        for s in sessions:
            sess_list.append({
                "id": s.id,
                "task_type": s.task_type,
                "topic": s.topic,
                "style": s.style,
                "status": s.status,
                "iterations": s.iterations,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "characters": char_profiles,
                "materials": mat_list,
                "sessions": sess_list
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ApiResponse)
async def update_project(project_id: str, request: ProjectUpdateRequest, db=Depends(get_db)):
    """更新项目"""
    try:
        init_db()
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if request.name is not None:
            project.name = request.name
        if request.description is not None:
            project.description = request.description
        project.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(project)

        return ApiResponse(
            success=True,
            message="项目更新成功",
            data={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "updated_at": project.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: str, db=Depends(get_db)):
    """删除项目（级联删除角色、素材、会话）"""
    try:
        init_db()
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 级联删除
        # 1. 删除会话（会自动删除关联的版本）
        db.query(Session).filter(Session.project_id == project_id).delete()
        
        # 2. 删除角色
        db.query(Character).filter(Character.project_id == project_id).delete()
        
        # 3. 删除素材
        db.query(Material).filter(Material.project_id == project_id).delete()
        
        # 4. 删除项目
        db.delete(project)
        
        db.commit()

        return ApiResponse(
            success=True,
            message="项目删除成功（已同步删除相关角色、素材和会话）"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
