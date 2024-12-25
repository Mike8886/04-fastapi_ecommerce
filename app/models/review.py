import datetime
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    rating_id = Column(Integer, ForeignKey('ratings.id'), nullable=False)
    comment = Column(Text)
    comment_date = Column(Date, default=datetime.datetime.now())
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship('User', backref='reviews')
    product = relationship('Product', backref='reviews')
    rating = relationship('Rating', backref='reviews')
