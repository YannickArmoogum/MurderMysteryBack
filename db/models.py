from sqlalchemy import Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class CardShare(Base):
    """An email-gated public link to a single character's dossier card.

    The host assigns a participant (name + email) to a character and shares the
    link; the recipient must enter the matching email to unlock the card.
    """
    __tablename__ = "card_shares"

    token: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False)          # stored lowercased
    participant_name: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    mystery_title: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    character_json: Mapped[str] = mapped_column(Text, nullable=False)  # the single character (JSON)
    timeline_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")
    portrait_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(Text, nullable=False, default="en", server_default="en")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    era: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    icon: Mapped[str] = mapped_column(Text, nullable=False, default="🎭", server_default="🎭")
    setting: Mapped[str] = mapped_column(Text, nullable=False)
    icon_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # French translations (nullable — English columns are the fallback).
    label_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    era_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    setting_fr: Mapped[str | None] = mapped_column(Text, nullable=True)


class Difficulty(Base):
    __tablename__ = "difficulties"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    label_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)


class Tone(Base):
    __tablename__ = "tones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    label_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)


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