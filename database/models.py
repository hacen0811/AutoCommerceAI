from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    product_name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(40), default="기획")
    coupang_url: Mapped[str] = mapped_column(Text, default="")
    partner_url: Mapped[str] = mapped_column(Text, default="")
    taobao_url: Mapped[str] = mapped_column(Text, default="")
    douyin_url: Mapped[str] = mapped_column(Text, default="")
    video_path: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    keyword: Mapped[str] = mapped_column(String(100), default="정보")
    score: Mapped[int] = mapped_column(Integer, default=0)
    data_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Checklist(Base):
    __tablename__ = "checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    source_video: Mapped[bool] = mapped_column(Boolean, default=False)
    capcut_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    inpock: Mapped[bool] = mapped_column(Boolean, default=False)
    youtube: Mapped[bool] = mapped_column(Boolean, default=False)
    instagram: Mapped[bool] = mapped_column(Boolean, default=False)
    performance: Mapped[bool] = mapped_column(Boolean, default=False)


class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
