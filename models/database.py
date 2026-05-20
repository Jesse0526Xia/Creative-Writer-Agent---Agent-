"""
数据库模型
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "writer.db")

# 确保目录存在
os.makedirs(os.path.join(BASE_DIR, "data", "db"), exist_ok=True)

Base = declarative_base()

# 创建同步数据库引擎
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Project(Base):
    """工作/项目表"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    """角色档案表"""
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    profile_data = Column(JSON, nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Material(Base):
    """素材库表"""
    __tablename__ = "materials"

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    file_name = Column(String(255))
    file_type = Column(String(50))
    vector_id = Column(Integer)
    meta_info = Column(JSON, default={})
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    """写作会话表"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    topic = Column(Text, nullable=False)
    style = Column(String(50), nullable=False)
    character_ids = Column(JSON, default=[])
    material_ids = Column(JSON, default=[])
    outline = Column(JSON)
    final_content = Column(Text)
    status = Column(String(20), default="pending")
    iterations = Column(Integer, default=0)
    current_agent = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("Version", back_populates="session", cascade="all, delete-orphan")
    project = relationship("Project", backref="sessions")


class Version(Base):
    """版本历史表"""
    __tablename__ = "versions"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="versions")
