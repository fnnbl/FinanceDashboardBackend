from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category, CategoryType


async def get_all_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.type, Category.name))
    return list(result.scalars().all())


async def get_categories_by_type(db: AsyncSession, category_type: CategoryType) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.type == category_type).order_by(Category.name)
    )
    return list(result.scalars().all())


async def seed_default_categories(db: AsyncSession) -> None:
    result = await db.execute(select(Category).where(Category.is_system == True))
    if result.scalars().first() is not None:
        return

    defaults = [
        # Einnahmen
        ("Gehalt", CategoryType.INCOME),
        ("Nebenverdienst", CategoryType.INCOME),
        ("Sonstiges", CategoryType.INCOME),
        # Ausgaben
        ("Miete", CategoryType.EXPENSE),
        ("Lebenshaltung", CategoryType.EXPENSE),
        ("Telefon/Internet", CategoryType.EXPENSE),
        ("Vermögensabsicherung", CategoryType.EXPENSE),
        ("Persönliche Absicherung", CategoryType.EXPENSE),
        ("Freizeit", CategoryType.EXPENSE),
        ("Urlaub", CategoryType.EXPENSE),
        ("Sport", CategoryType.EXPENSE),
        ("ÖPNV", CategoryType.EXPENSE),
        ("Abonnements", CategoryType.EXPENSE),
        ("Studium", CategoryType.EXPENSE),
        ("Vermögensaufbau", CategoryType.EXPENSE),
        ("Altersvorsorge", CategoryType.EXPENSE),
        ("Kredite/Darlehen", CategoryType.EXPENSE),
        ("Konsum", CategoryType.EXPENSE),
        ("Sonstige", CategoryType.EXPENSE),
    ]

    for name, cat_type in defaults:
        db.add(Category(name=name, type=cat_type, is_system=True))

    await db.commit()
