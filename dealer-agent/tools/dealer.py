from typing import List, Tuple, Optional, Literal
import random
from enum import Enum
from pydantic import BaseModel, Field

# ----- Models -----

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

class GameState(BaseModel):
    shoe: List[Card]
    player_hand: Hand = Field(default_factory=Hand)
    dealer_hand: Hand = Field(default_factory=Hand)
    bet: float = 0.0
    history: List[dict] = Field(default_factory=list)

# ----- Utility Functions -----

def shuffleShoe() -> List[Card]:
    """
    Initialize or re-shuffle the six-deck shoe.
    """
    single_deck = [Card(suit=s, rank=r) for s in Suit for r in Rank]
    shoe = single_deck * 6
    random.shuffle(shoe)
    return shoe

def drawCard(shoe: List[Card]) -> Tuple[Card, List[Card]]:
    """
    Draw the top card from the shoe.
    """
    card = shoe.pop()
    return card, shoe

# ----- Evaluation -----

def evaluateHand(hand: Hand) -> HandEvaluation:
    """
    Compute best total <=21, detect soft total, blackjack, or bust.
    """
    values = []
    aces = 0
    for c in hand.cards:
        if c.rank in (Rank.jack, Rank.queen, Rank.king):
            values.append(10)
        elif c.rank == Rank.ace:
            aces += 1
        else:
            values.append(int(c.rank))
    # Ace handling
    total = sum(values) + aces  # all aces as 1
    is_soft = False
    if aces > 0 and total + 10 <= 21:
        total += 10
        is_soft = True
    is_blackjack = len(hand.cards) == 2 and total == 21
    is_bust = total > 21
    return HandEvaluation(total=total, is_soft=is_soft, is_blackjack=is_blackjack, is_bust=is_bust)

# ----- Dealing -----

def dealInitialHands(state: GameState, bet: float) -> GameState:
    """
    Deal two cards each to player and dealer.
    """
    state.bet = bet
    for _ in range(2):
        card, state.shoe = drawCard(state.shoe)
        state.player_hand.cards.append(card)
        card, state.shoe = drawCard(state.shoe)
        state.dealer_hand.cards.append(card)
    return state

# ----- Player Actions -----

def processPlayerAction(action: Literal['hit', 'stand'], state: GameState) -> GameState:
    """
    Handle player action: hit or stand.
    """
    if action == 'hit':
        card, state.shoe = drawCard(state.shoe)
        state.player_hand.cards.append(card)
    return state

# ----- Dealer Play -----

def processDealerPlay(state: GameState) -> GameState:
    """
    Dealer draws until total >=17 (stand on soft 17).
    """
    eval = evaluateHand(state.dealer_hand)
    while eval.total < 17:
        card, state.shoe = drawCard(state.shoe)
        state.dealer_hand.cards.append(card)
        eval = evaluateHand(state.dealer_hand)
    return state

# ----- Settlement -----

def settleBet(state: GameState) -> Tuple[float, Literal['win', 'loss', 'push']]:
    """
    Compare player and dealer hands, compute payout.
    """
    player_eval = evaluateHand(state.player_hand)
    dealer_eval = evaluateHand(state.dealer_hand)
    if player_eval.is_bust:
        return -state.bet, 'loss'
    if dealer_eval.is_bust:
        return state.bet, 'win'
    if player_eval.is_blackjack and not dealer_eval.is_blackjack:
        return state.bet * 1.5, 'win'
    if dealer_eval.is_blackjack and not player_eval.is_blackjack:
        return -state.bet, 'loss'
    # neither bust nor blackjack
    if player_eval.total > dealer_eval.total:
        return state.bet, 'win'
    if player_eval.total < dealer_eval.total:
        return -state.bet, 'loss'
    return 0.0, 'push'

# ----- Shoe Check & Reset -----

def checkShoeExhaustion(state: GameState, threshold: int = 20) -> bool:
    """
    Return True if shoe has fewer than threshold cards.
    """
    return len(state.shoe) < threshold

def resetForNextHand(state: GameState) -> GameState:
    """
    Prepare for next hand: reshuffle if needed, clear hands.
    """
    if checkShoeExhaustion(state):
        state.shoe = shuffleShoe()
    state.player_hand = Hand()
    state.dealer_hand = Hand()
    state.bet = 0.0
    return state

# ----- Display & Prompt -----

def displayState(state: GameState, revealDealerHole: bool = False) -> str:
    """
    Render human-readable game state.
    """
    p_eval = evaluateHand(state.player_hand)
    lines = [f"Player Hand: {[f'{c.rank}{c.suit}' for c in state.player_hand.cards]} (Total: {p_eval.total})"]
    if revealDealerHole:
        d_eval = evaluateHand(state.dealer_hand)
        lines.append(f"Dealer Hand: {[f'{c.rank}{c.suit}' for c in state.dealer_hand.cards]} (Total: {d_eval.total})")
    else:
        up = state.dealer_hand.cards[0]
        lines.append(f"Dealer Up-Card: {up.rank}{up.suit}")
    return '\n'.join(lines)
