from sqlalchemy import Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    era: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    icon: Mapped[str] = mapped_column(Text, nullable=False, default="🎭", server_default="🎭")
    setting: Mapped[str] = mapped_column(Text, nullable=False)
    icon_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class Difficulty(Base):
    __tablename__ = "difficulties"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class Tone(Base):
    __tablename__ = "tones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    era: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    setting: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    min_players: Mapped[int] = mapped_column(Integer, nullable=False, default=6, server_default="6")
    max_players: Mapped[int] = mapped_column(Integer, nullable=False, default=16, server_default="16")
    difficulty: Mapped[str] = mapped_column(Text, nullable=False, default="Medium", server_default="Medium")
    duration: Mapped[str] = mapped_column(Text, nullable=False, default="3-4 hours", server_default="3-4 hours")
    theme: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    victim: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    murder_method: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    cover_image: Mapped[str] = mapped_column(Text, nullable=False, default="🎭", server_default="🎭")