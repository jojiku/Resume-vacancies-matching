from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import BIGINT

from app.database import Base


class Resumes(Base):
    __tablename__ = "resumes"

    p_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    gend_age: Mapped[str] = mapped_column(Text, nullable=True)
    salary: Mapped[str] = mapped_column(Text, nullable=True)
    job_title: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(Text, nullable=True)
    employment: Mapped[str] = mapped_column(Text, nullable=True)
    schedule: Mapped[str] = mapped_column(Text, nullable=True)
    experience: Mapped[str] = mapped_column(Text, nullable=True)
    last_wp: Mapped[str] = mapped_column(Text, nullable=True)
    last_jt: Mapped[str] = mapped_column(Text, nullable=True)
    edu: Mapped[str] = mapped_column(Text, nullable=True)
    upd_date: Mapped[str] = mapped_column(Text, nullable=True)
    auto: Mapped[str] = mapped_column(Text, nullable=True)


class Vacancies(Base):
    __tablename__ = "vacancies"

    p_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    employer: Mapped[str] = mapped_column(Text, nullable=True)
    vac_title: Mapped[str] = mapped_column(Text, nullable=True)
    sal_from: Mapped[str] = mapped_column(Text, nullable=True)
    sal_to: Mapped[str] = mapped_column(Text, nullable=True)
    req_exp: Mapped[str] = mapped_column(Text, nullable=True)
    sch_type: Mapped[str] = mapped_column(Text, nullable=True)
    keywords: Mapped[str] = mapped_column(Text, nullable=True)
    descr: Mapped[str] = mapped_column(Text, nullable=True)
    area: Mapped[str] = mapped_column(Text, nullable=True)
    key_req: Mapped[str] = mapped_column(Text, nullable=True)
    spec: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=True)
    publ_date: Mapped[str] = mapped_column(Text, nullable=True)
