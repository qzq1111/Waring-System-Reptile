# coding: utf-8
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

"""
连接数据库
"""
db = 'mysql+pymysql://root:mad123@39.108.60.79/graduation_project?charset=utf8'
engine = create_engine(db, encoding='utf-8')
Base = declarative_base()
DBSession = sessionmaker(bind=engine)
session = DBSession()


class Ip_Pool(Base):
    __tablename__ = 'ip_pool'
    id = Column(String(36), primary_key=True)
    ip = Column(String(36), nullable=True)
    updatetime = Column(DateTime, nullable=True)
    datastatus = Column(Integer, nullable=True)


# Base.metadata.create_all(engine)

class Sh_A_Share(Base):
    __tablename__ = 'sh_a_share'
    bulletinid = Column(String(32), primary_key=True)
    stockcode = Column(String(6), nullable=True)
    stockname = Column(String(30), nullable=True)
    title = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    url = Column(String(255), primary_key=True, nullable=True)
    bulletinyear = Column(Date, nullable=True)  # 公告年份
    bulletindate = Column(DateTime, nullable=True)  # 公告年份日期
    uploadtime = Column(DateTime, nullable=True)
    datastatus = Column(Integer, nullable=True)

class Sh_Share(Base):
    __tablename__='sh_share'
    stockcode=Column(String(6),primary_key=True)
    stockname=Column(String(30),nullable=True)
    companycode=Column(String(7),nullable=True)
    companyname=Column(String(30),nullable=True)
    datastatus=Column(Integer,nullable=True)
