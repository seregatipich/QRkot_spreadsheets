from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CharityProject, Donation


async def close_object(
    obj_in,
    session: AsyncSession,
):
    obj_in.fully_invested = True
    obj_in.close_date = datetime.now()
    return obj_in


async def investment_process(
    obj_in,
    session: AsyncSession,
):
    open_project = await session.execute(
        select(CharityProject)
        .where(
            CharityProject.fully_invested == 0,
        )
        .order_by('create_date')
    )
    open_project = open_project.scalars().first()
    free_donat = await session.execute(
        select(Donation)
        .where(
            Donation.fully_invested == 0,
        )
        .order_by('create_date')
    )
    free_donat = free_donat.scalars().first()
    if not open_project or not free_donat:
        await session.commit()
        await session.refresh(obj_in)
        return obj_in
    balance_project = open_project.full_amount - open_project.invested_amount
    balance_donation = free_donat.full_amount - free_donat.invested_amount
    if balance_project > balance_donation:
        open_project.invested_amount += balance_donation
        free_donat.invested_amount += balance_donation
        await close_object(free_donat, session)
    elif balance_project == balance_donation:
        open_project.invested_amount += balance_donation
        free_donat.invested_amount += balance_donation
        await close_object(free_donat, session)
        await close_object(open_project, session)
    else:
        open_project.invested_amount += balance_donation
        free_donat.invested_amount += balance_donation
        await close_object(open_project, session)
    session.add(open_project)
    session.add(free_donat)
    await session.commit()
    await session.refresh(open_project)
    await session.refresh(free_donat)
    return await investment_process(obj_in, session)
