from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.dashboard import DashboardAnalyticsResponse, TodayDashboardResponse
from app.services.dashboard import (
    build_analytics_dashboard,
    build_day_dashboard,
    build_today_dashboard,
)

router = APIRouter()


@router.get("/today", response_model=TodayDashboardResponse)
async def today_dashboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TodayDashboardResponse:
    """Дашборд текущего дня для аутентифицированного пользователя.

    Возвращает агрегаты, счётчики и timeline активностей за сегодня.
    Данные строятся на основе реального содержимого журнала.
    """
    return await build_today_dashboard(db, current_user.id)


@router.get("/day", response_model=TodayDashboardResponse)
async def day_dashboard(
    current_user: CurrentUser,
    work_date: date = Query(..., description="Рабочая дата в формате YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
) -> TodayDashboardResponse:
    """Дашборд выбранного дня по work_date."""
    return await build_day_dashboard(db, current_user.id, work_date)


@router.get("/analytics", response_model=DashboardAnalyticsResponse)
async def analytics_dashboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DashboardAnalyticsResponse:
    """Историческая аналитика по журналу и услугам."""
    return await build_analytics_dashboard(db, current_user.id)
