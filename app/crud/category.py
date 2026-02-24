from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.category import Category, CategoryType
from app.models.budget_item import BudgetItem


async def get_all_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.type, Category.name))
    return list(result.scalars().all())


async def get_categories_by_type(db: AsyncSession, category_type: CategoryType) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.type == category_type).order_by(Category.name)
    )
    return list(result.scalars().all())


async def get_category_by_name(db: AsyncSession, name: str) -> Category | None:
    result = await db.execute(select(Category).where(Category.name == name))
    return result.scalars().first()


async def get_category_by_id(db: AsyncSession, category_id: int) -> Category | None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalars().first()


async def update_category(db: AsyncSession, category: Category, name: str) -> Category:
    category.name = name
    await db.commit()
    await db.refresh(category)
    return category


async def count_budget_items_by_category(db: AsyncSession, category_id: int) -> int:
    result = await db.execute(
        select(func.count(BudgetItem.id)).where(BudgetItem.category_id == category_id)
    )
    return result.scalar() or 0


async def delete_category(db: AsyncSession, category: Category, reassign_to_id: int | None = None) -> None:
    if reassign_to_id:
        await db.execute(
            update(BudgetItem)
            .where(BudgetItem.category_id == category.id)
            .values(category_id=reassign_to_id)
        )
    await db.delete(category)
    await db.commit()


async def create_category(db: AsyncSession, name: str, category_type: CategoryType) -> Category:
    db_category = Category(name=name, type=category_type, is_system=False)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


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
