from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from flask import current_app

Base = declarative_base()


class Users(Base):
    """
    Saves userdata
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    admin = Column(Boolean)

    def __repr__(self):
        return f"ID: {self.id}, user {self.username}, admin: {self.admin}"


class Config(Base):
    """
    Saves configuration switches like "Registration open?" and such
    """
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(String)


class Sites(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, unique=True)
    seo_description = Column(String)
    seo_author = Column(String)
    image = Column(String, unique=True)
    bio = Column(String)
    footer = Column(String)

    owner = relationship("Users", back_populates="sites")

    def __repr__(self):
        return f"ID: {self.id}, Site {self.name}, by user-id {self.owner_id}"


class Links(Base):
    __tablename__ = "Links"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('sites.id'))
    icon = Column(String)
    link = Column(String)
    text = Column(String)
    order = Column(Integer)

    __mapper_args__ = {
        "order_by": order
    }

    site = relationship("Sites", back_populates="links")


User.sites = relationship("Sites", back_populates="user")
Sites.links = relationship("Links", back_populates="site")


def get_session():
    try:
        db_uri = current_app.config["DATABASE"]
    except:
        db_uri = 'sqlite:////uwsgi/data/sqlite.db'
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
