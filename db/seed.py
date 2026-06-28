"""Idempotent reference-data seeding via the ORM (no raw SQL).

Run on a fresh database after ``alembic upgrade head``::

    python -m db.seed

Safe to re-run: every row is upserted by primary key with ``Session.merge()``,
so a second run restores the canonical values rather than inserting duplicates.
"""
from sqlalchemy.orm import Session

from core.config import config
from db.db_manager import DbManager
from db.models import Theme, Difficulty, Tone, Setting, Scenario

# ── Themes (merged from the Angular frontend + prompts) ──────────────────────
THEMES = [
    Theme(id="aristocratic-ball",   label="Aristocratic Masked Ball",      era="Belle Époque · 1895",       icon="🎭", setting="Château de Villeneuve, Paris"),
    Theme(id="speakeasy-1920",      label="1920s Speakeasy",               era="Prohibition Era · 1928",    icon="🥃", setting="The Blue Moon Club, Chicago"),
    Theme(id="luxury-yacht",        label="Luxury Yacht Party",            era="Contemporary · Present Day", icon="⚓", setting="The Empress, Mediterranean Sea"),
    Theme(id="alpine-chalet",       label="Alpine Chalet Retreat",         era="Contemporary · Winter",     icon="🏔️", setting="Chalet Blanc, Swiss Alps"),
    Theme(id="italian-wedding",     label="Italian Wedding in Tuscany",    era="Contemporary · Summer",     icon="💒", setting="Villa Rosso, Tuscany"),
    Theme(id="tech-summit",         label="Billionaire Tech Summit",       era="Near Future · 2031",        icon="💻", setting="The Nexus Tower, Silicon Valley"),
    Theme(id="art-auction",         label="Art Auction Night",             era="Contemporary · Present Day", icon="🖼️", setting="Galerie Noir, New York"),
    Theme(id="royal-family",        label="Royal Family Gathering",        era="Contemporary · Present Day", icon="👑", setting="Ashford Palace, England"),
    Theme(id="film-festival",       label="Film Festival Premiere",        era="1940s Hollywood · 1947",    icon="🎬", setting="Beverly Hills Mansion"),
    Theme(id="champagne-estate",    label="Champagne Vineyard Estate",     era="Contemporary · Autumn",     icon="🍷", setting="Domaine de la Lune, Champagne"),
    Theme(id="victorian-manor",     label="Victorian Manor",               era="Victorian Era · 1889",      icon="🏰", setting="Blackwood Manor, English Countryside"),
    Theme(id="haunted-manor",       label="Haunted Victorian Manor",       era="Gothic · 1871",             icon="🕯️", setting="Ravenshollow, Dartmoor"),
    Theme(id="destination-wedding", label="Destination Wedding Mauritius", era="Contemporary · Present Day", icon="🌴", setting="Grand Baie Estate, Mauritius"),
    Theme(id="political-gala",      label="Political Fundraising Gala",    era="Contemporary · Present Day", icon="🏛️", setting="The Capitol Grand Ballroom"),
]

# ── Difficulties ─────────────────────────────────────────────────────────────
DIFFICULTIES = [
    Difficulty(id="casual",      label="Casual",      description="Light misdirection. One obvious red herring. Clues are fairly clear."),
    Difficulty(id="challenging", label="Challenging", description="Two red herrings. Clues require cross-referencing. Moderate ambiguity."),
    Difficulty(id="expert",      label="Expert",      description="Heavy misdirection. Multiple red herrings. Every character looks guilty."),
]

# ── Tones ────────────────────────────────────────────────────────────────────
TONES = [
    Tone(id="dramatic",  label="Dramatic",  description="Grand emotions, moral weight, Shakespearean betrayals."),
    Tone(id="dark",      label="Dark",      description="Psychological menace, dark secrets, grim atmosphere."),
    Tone(id="romantic",  label="Romantic",  description="Passion, jealousy, forbidden love triangles drive the plot."),
    Tone(id="satirical", label="Satirical", description="Sharp wit, social critique, absurd privilege exposed."),
]

# ── App settings ─────────────────────────────────────────────────────────────
SETTINGS = [
    Setting(key="llm_model",          value=config.LLM_MODEL,   description="HuggingFace model ID for story/character generation"),
    Setting(key="image_model",        value=config.IMAGE_MODEL, description="HuggingFace model ID for character portraits"),
    Setting(key="tts_model",          value=config.TTS_MODEL,   description="HuggingFace model ID for TTS narration"),
    Setting(key="min_players",        value="6",                description="Minimum number of players for a mystery"),
    Setting(key="max_players",        value="14",               description="Maximum number of players for a mystery"),
    Setting(key="default_difficulty", value="casual",           description="Default difficulty level"),
    Setting(key="default_tone",       value="dramatic",         description="Default narrative tone"),
]

# ── Scenarios ────────────────────────────────────────────────────────────────
SCENARIOS = [
    Scenario(
        id="victorian-manor", title="Death at Blackwood Manor",
        era="Victorian Era", setting="1889 — English Countryside",
        description="A prestigious dinner party at the ancestral Blackwood Manor turns deadly when the wealthy Lord Blackwood is found poisoned in his study. The storm has cut off all roads. The killer is among you.",
        min_players=6, max_players=16, difficulty="Medium", duration="3-4 hours",
        theme="Gothic Victorian", victim="Lord Alistair Blackwood",
        murder_method="Arsenic poisoning in the port wine", cover_image="🕯️",
    ),
    Scenario(
        id="speakeasy-1920", title="Last Call at the Blue Moon",
        era="1920s Prohibition", setting="1928 — Chicago Underground",
        description="The city's most notorious speakeasy hosts its annual masquerade, but the night ends in bloodshed when the club's owner is found in the back room with a bullet in his chest.",
        min_players=8, max_players=16, difficulty="Medium", duration="3-4 hours",
        theme="Roaring Twenties Noir", victim='Big Tony "Diamond" Marchetti',
        murder_method="Single gunshot, .38 caliber revolver", cover_image="🎷",
    ),
    Scenario(
        id="space-station", title="Murder on the Meridian-7",
        era="Sci-Fi Future", setting="2387 — Deep Space Station",
        description="Aboard humanity's most advanced space station, a renowned astrophysicist is found dead in the zero-gravity lab. The airlock has been sealed and no one can leave until the killer is found.",
        min_players=8, max_players=14, difficulty="Hard", duration="4-5 hours",
        theme="Sci-Fi Thriller", victim="Dr. Elara Voss",
        murder_method="Toxic compound injected into life-support nutrient pack", cover_image="🛸",
    ),
    Scenario(
        id="medieval-castle", title="The Curse of Castle Dreadmore",
        era="Medieval", setting="1347 — Scotland Highlands",
        description="During the feast of All Hallows, the king's most trusted advisor is discovered with a dagger through his heart in the great hall.",
        min_players=6, max_players=16, difficulty="Easy", duration="2-3 hours",
        theme="Medieval Dark Fantasy", victim="Sir Edmund the Advisor",
        murder_method="Stabbed with the King's ceremonial dagger", cover_image="🗡️",
    ),
    Scenario(
        id="hollywood-golden", title="Lights Out in Hollywood",
        era="1940s Hollywood", setting="1947 — Beverly Hills Mansion",
        description="The most glamorous Oscar after-party of the decade goes dark when famed director Cecil B. Monroe is found strangled in the projection room.",
        min_players=8, max_players=16, difficulty="Medium", duration="3-4 hours",
        theme="Golden Age Hollywood", victim="Director Cecil B. Monroe",
        murder_method="Strangulation with a camera film reel", cover_image="🎭",
    ),
]


def seed(session: Session) -> None:
    """Upsert every reference row by primary key (idempotent)."""
    for row in (*THEMES, *DIFFICULTIES, *TONES, *SETTINGS, *SCENARIOS):
        session.merge(row)
    session.commit()


def main() -> None:
    session = DbManager(url=config.DB_URL).get_session()
    try:
        seed(session)
    finally:
        session.close()
    print("Seed complete: "
          f"{len(THEMES)} themes, {len(DIFFICULTIES)} difficulties, "
          f"{len(TONES)} tones, {len(SETTINGS)} settings, {len(SCENARIOS)} scenarios.")


if __name__ == "__main__":
    main()