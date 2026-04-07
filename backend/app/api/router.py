from fastapi import APIRouter

from app.api.routes import auth, dashboard, developer, health, journal, planned_events, plans, reports, search, team, templates

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(journal.router, prefix="/journal", tags=["journal"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(planned_events.router, prefix="/planned-events", tags=["planned-events"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(team.router, prefix="/team", tags=["team"])
api_router.include_router(developer.router, prefix="/developer", tags=["developer"])
