from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.backend.db_depends import get_db
from app.models.products import Product
from app.models.category import Category
from app.schemas import CreateProduct
from app.routers.auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def all_products(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    products = await db.scalars(select(Product).where(
        Product.is_active == True,
        Product.stock > 0
        ))
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    return products.all()


@router.post("/")
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get('is_admin'):
        await db.scalar(insert(Product).values(
            name=create_product.name,
            description=create_product.description,
            price=create_product.price,
            image_url=create_product.image_url,
            stock=create_product.stock,
            category_id=create_product.category,
            slug=slugify(create_product.name),
        ))
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this',
            headers=None
        )


@router.get('/{category_slug}')
async def product_by_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_slug: str,
):
    category = await db.scalar(select(Category).where(
        Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    subcategories = await db.scalars(select(Category).where(
        Category.parent_id == category.id))
    categories_and_subcategories = [category.id] + [i.id for i in subcategories.all()]
    products_category = await db.scalars(
        select(Product).where(Product.category_id.in_(
            categories_and_subcategories), Product.is_active == True,
                              Product.stock > 0))
    return products_category.all()


@router.get("/detail/{product_slug}")
async def product_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str
):
    product = await db.scalar(
        select(Product).where(Product.slug == product_slug)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product is not found'
        )
    return product


@router.put("/{product_slug}")
async def update_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    update_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        product_update = await db.scalar(select(Product)
                                        .where(Product.slug == product_slug))
        if product_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
            )
        category = await db.scalar(select(Category)
                                .where(Category.id == update_product.category))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )
        await db.execute(update(Product).where(Product.slug == product_slug)
                        .values(
            name=update_product.name,
            description=update_product.description,
            price=update_product.price,
            image_url=update_product.image_url,
            stock=update_product.stock,
            category_id=update_product.category,
            slug=slugify(update_product.name),
        ))
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product update Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this',
            headers=None
        )


@router.delete("/{product_id}")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        product_delete = await db.scalar(select(Product)
                                        .where(Product.slug == product_slug))
        if product_delete is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
            )
        await db.execute(update(Product).where(
            Product.slug == product_slug
            ).values(is_active=False))
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product deleted Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this',
            headers=None
        )
