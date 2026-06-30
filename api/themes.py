from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependencies import get_session
from db.themes import ThemesRepository

router = APIRouter(prefix="/api/themes")


@router.get("", operation_id="listThemes")
def list_themes(lang: str = "en", session: Session = Depends(get_session)):
    return ThemesRepository(session).list_localized(lang)


@router.get("/{theme_id}", operation_id="getTheme")
def get_theme(theme_id: str, lang: str = "en", session: Session = Depends(get_session)):
    theme = ThemesRepository(session).get_localized(theme_id, lang)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.post("", status_code=201, operation_id="createTheme")
def create_theme(body: dict, session: Session = Depends(get_session)):
    theme_id = body.get("id")
    label = body.get("label")
    if not theme_id or not label:
        raise HTTPException(status_code=422, detail="'id' and 'label' are required")
    repo = ThemesRepository(session)
    if repo.get_by_id(theme_id):
        raise HTTPException(status_code=409, detail="Theme with this id already exists")
    return repo.create(
        theme_id=theme_id,
        label=label,
        era=body.get("era", ""),
        icon=body.get("icon", "🎭"),
        setting=body.get("setting", ""),
    )


@router.put("/{theme_id}", operation_id="updateTheme")
def update_theme(theme_id: str, body: dict, session: Session = Depends(get_session)):
    theme = ThemesRepository(session).update(theme_id, **body)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.delete("/{theme_id}", status_code=204, operation_id="deleteTheme")
def delete_theme(theme_id: str, session: Session = Depends(get_session)):
    if not ThemesRepository(session).delete(theme_id):
        raise HTTPException(status_code=404, detail="Theme not found")