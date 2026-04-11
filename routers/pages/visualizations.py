from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/visualizations", response_class=HTMLResponse, include_in_schema=False)
def visualizations_page(request: Request):
    now = datetime.now()
    return templates.TemplateResponse(
        "visualizations.html",
        {
            "request": request,
            "title": "Visualizations",
            "active_page": "visualizations",
            "default_year": now.year,
            "default_month": now.month,
        }
    )