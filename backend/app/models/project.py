from sqlalchemy import Column, BigInteger, Text, Numeric, Date, DateTime, ForeignKey, func
from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    pm_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    budget_allocated = Column(Numeric, nullable=False, default=0)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Text, nullable=False, default="planning")  # planning | in_progress | on_hold | completed
    progress_percent = Column(Numeric, nullable=False, default=0)
    created_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Text, nullable=False, default="not_started")  # not_started | in_progress | delayed | completed
    start_date = Column(Date)
    end_date = Column(Date)
    depends_on_task_id = Column(BigInteger, ForeignKey("tasks.id"))
    assigned_to = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    due_date = Column(Date)
    status = Column(Text, nullable=False, default="upcoming")  # upcoming | achieved | missed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
