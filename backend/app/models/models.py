from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
class Role(Base):
    __tablename__='roles'; id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(30),unique=True)
    users=relationship('User',back_populates='role')
class User(Base):
    __tablename__='users'; id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(100)); email: Mapped[str]=mapped_column(String(120),unique=True,index=True); password: Mapped[str]=mapped_column(String(255)); role_id: Mapped[int]=mapped_column(ForeignKey('roles.id'))
    role=relationship('Role',back_populates='users')
class Task(Base):
    __tablename__='tasks'; id: Mapped[int]=mapped_column(primary_key=True); title: Mapped[str]=mapped_column(String(180)); description: Mapped[str]=mapped_column(Text,default=''); status: Mapped[str]=mapped_column(String(20),default='pending'); assigned_to: Mapped[int]=mapped_column(ForeignKey('users.id')); created_by: Mapped[int]=mapped_column(ForeignKey('users.id')); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    assignee=relationship('User',foreign_keys=[assigned_to]); creator=relationship('User',foreign_keys=[created_by])
class Document(Base):
    __tablename__='documents'; id: Mapped[int]=mapped_column(primary_key=True); filename: Mapped[str]=mapped_column(String(255)); file_path: Mapped[str]=mapped_column(String(500)); uploaded_by: Mapped[int]=mapped_column(ForeignKey('users.id')); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    uploader=relationship('User')
class ActivityLog(Base):
    __tablename__='activity_logs'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); action: Mapped[str]=mapped_column(String(80)); details: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    user=relationship('User')
