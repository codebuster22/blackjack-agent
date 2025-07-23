"""
Card and game models for the blackjack game.
This file contains the core data structures used throughout the game.
"""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field

class Suit(str, Enum):
    hearts = 'H'
    diamonds = 'D'
    clubs = 'C'
    spades = 'S'

class Rank(str, Enum):
    two = '2'
    three = '3'
    four = '4'
    five = '5'
    six = '6'
    seven = '7'
    eight = '8'
    nine = '9'
    ten = '10'
    jack = 'J'
    queen = 'Q'
    king = 'K'
    ace = 'A'

class Card(BaseModel):
    suit: Suit
    rank: Rank

class HandEvaluation(BaseModel):
    total: int
    is_soft: bool
    is_blackjack: bool
    is_bust: bool

class Hand(BaseModel):
    cards: List[Card] = Field(default_factory=list) 