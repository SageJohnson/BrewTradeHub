from __future__ import annotations
from enum import Enum
# from datetime import date

from app import db
from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship

class UserType(Enum):
    user = "User"
    administrator = "Administrator"

# class OfferStatus(Enum):
#     opened = "opened"
#     accepted = "accepted"
#     shipped = "shipped"
#     received = "received"

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

# Define the association table (from ChatGPT with edits)
offer_user_association = db.Table(
    "offer_user_association",
    db.Column("offer_code", String, ForeignKey("offer.code")),
    db.Column("user_id", String, ForeignKey("user.id"))
)

class Offer(db.Model):
    __tablename__ = "offer"
    code: Mapped[str] = db.mapped_column(db.String, primary_key=True)
    description: Mapped[str] = db.mapped_column(db.String)
    year: Mapped[int] = db.mapped_column(db.Integer)
    productType: Mapped[str] = db.mapped_column(db.String)
    brand: Mapped[str] = db.mapped_column(db.String)
    price: Mapped[float] = db.mapped_column(db.Float, nullable=True)
    status: Mapped[String] = db.mapped_column(db.String)
    buyer_id: Mapped[String] = db.mapped_column(db.String, nullable=True)
    seller_id: Mapped[String] = db.mapped_column(db.String, nullable=True)
    users = relationship("User", secondary=offer_user_association, back_populates="offers") # backpops the offers relationship (in User class)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id: Mapped[String] = db.mapped_column(db.String, primary_key=True)
    description: Mapped[String] = db.mapped_column(db.String, nullable=True)
    representative_name: Mapped[String] = db.mapped_column(db.String, nullable=True)
    email: Mapped[String] = db.mapped_column(db.String, nullable=True)
    password = db.mapped_column(db.LargeBinary)
    user_type: Mapped[UserType] = db.mapped_column(db.Enum(UserType))
    offers = relationship("Offer", secondary=offer_user_association, back_populates="users") # backpops the users relationship (in Offer class)
    reviews = relationship("Review")

class Review(db.Model):
    __tablename__ = "review"
    user_id =  db.Column(db.String, db.ForeignKey("user.id"), primary_key=True)
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.String) # please use: time.time()
    star_rating: Mapped[int] = db.mapped_column(db.Integer) # should only range from 1 to 5 (will need to be change to account for .5 stars if we want).
    comment: Mapped[str] = db.mapped_column(db.String)
    reply = db.relationship("Reply") # make sure these are chronological, might need a new class to hold reply dates?

class Reply(db.Model):
    __tablename__ = "reply"
    review_id = db.Column(db.String, db.ForeignKey("review.id"), primary_key=True)
    id = db.Column(db.String, primary_key=True)
    date: Mapped[str] = db.Column(db.String) # please use: time.time()
    comment: Mapped[str] = db.mapped_column(db.String)
