"""SQLAlchemy ORM schema for the cleaned anime relational store."""
from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Anime(Base):
    __tablename__ = "anime"

    mal_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    media_type: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date] = mapped_column(Date, nullable=True)
    mean_score: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=True)
    popularity: Mapped[int] = mapped_column(Integer, nullable=True)
    num_list_users: Mapped[int] = mapped_column(Integer, nullable=True)
    num_scoring_users: Mapped[int] = mapped_column(Integer, nullable=True)
    num_episodes: Mapped[int] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=True)
    rating: Mapped[str] = mapped_column(String, nullable=True)
    average_episode_duration: Mapped[int] = mapped_column(Integer, nullable=True)
    nsfw: Mapped[str] = mapped_column(String, nullable=True)
    synopsis: Mapped[str] = mapped_column(Text, nullable=True)
    start_season_year: Mapped[int] = mapped_column(Integer, nullable=True)
    start_season_season: Mapped[str] = mapped_column(String, nullable=True)


class Genre(Base):
    __tablename__ = "genres"

    genre_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)


class AnimeGenre(Base):
    __tablename__ = "anime_genres"

    mal_id: Mapped[int] = mapped_column(ForeignKey("anime.mal_id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.genre_id"), primary_key=True)


class Studio(Base):
    __tablename__ = "studios"

    studio_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)


class AnimeStudio(Base):
    __tablename__ = "anime_studios"

    mal_id: Mapped[int] = mapped_column(ForeignKey("anime.mal_id"), primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.studio_id"), primary_key=True)
