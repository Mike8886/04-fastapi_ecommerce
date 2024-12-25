from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.products import Product
from app.models.rating import Rating
from app.models.review import Review
from app.schemas import CreateReview
from app.routers.auth import get_current_user


router = APIRouter(prefix="/review", tags=["review"])

@router.get('/')
async def all_reviews(
    db: AsyncSession = Depends(get_db),
):
    reviews = await db.scalars(
        select(Review)
        .where(Review.is_active == True)
        .order_by(Review.comment_date))
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no review'
        )
    return reviews.all()


@router.get('/{product_id}')
async def products_reviews(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    reviews = await db.scalars(
        select(Review)
        .where(Review.product_id == product_id)
    )
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no review in select product'
        )
    return reviews.all()


@router.post('/{product_id}', status_code=status.HTTP_201_CREATED)
async def add_review(
    product_id: int,
    create_review: CreateReview, 
    get_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    if get_user.get('is_customer'):
        product = await db.scalar(select(Product)
                                  .where(
                                      Product.id == product_id and
                                      Product.is_active == True
                                      ))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )

        # Добавление рейтинга
        rating_id = await db.scalar(insert(Rating)
                                    .values(
                                        user_id=get_user.get('id'),
                                        product_id=product_id,
                                        grade=create_review.grade,
                                    )
                                    .returning(Rating.id))
        # Добавление отзыва
        await db.scalar(insert(Review)
                        .values(
                            user_id=get_user.get('id'),
                            product_id=product_id,
                            rating_id=rating_id,
                            comment=create_review.comment,
                        ))

        # Обновление рейтинга у продукта
        await db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(
                rating=(
                    select(func.avg(Rating.grade))
                    .where(Rating.product_id == product_id)
                    )
            ))
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Review deleted Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be customer user for this',
            headers=None
        )


@router.delete('/{review_id}')
async def delete_reviews(
    review_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    if get_user.get('is_admin'):
        rating_id = await db.scalar(
            select(Review.rating_id)
            .where(Review.id == review_id)
        )
        await db.execute(
            update(Review)
            .where(Review.id == review_id)
            .values(is_active=False)
        )
        await db.execute(
            update(Rating)
            .where(Rating.id == rating_id)
            .values(is_active=False)
        )
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Review delete Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be customer admin for this',
            headers=None
        )
