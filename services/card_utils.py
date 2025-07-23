"""
Card utility functions for database storage.
Handles conversion between Card objects and string format.
"""

import json
from typing import List, Dict, Any
from dealer_agent.tools.dealer import Card, Hand, Suit, Rank

def card_to_string(card: Card) -> str:
    """
    Convert a Card object to string format for database storage.
    
    Args:
        card: Card object to convert
        
    Returns:
        str: Card in "AS" format (Ace of Spades)
    """
    return f"{card.rank.value}{card.suit.value}"

def string_to_card(card_str: str) -> Card:
    """
    Convert a string back to a Card object.
    
    Args:
        card_str: Card string in "AS" format
        
    Returns:
        Card: Card object
        
    Raises:
        ValueError: If card string format is invalid
    """
    if len(card_str) < 2:
        raise ValueError(f"Invalid card string format: {card_str}")
    
    # Handle 10 (two characters)
    if card_str.startswith('10'):
        rank_str = '10'
        suit_str = card_str[2:]
    else:
        rank_str = card_str[0]
        suit_str = card_str[1]
    
    # Convert rank string to Rank enum
    rank_map = {
        '2': Rank.two, '3': Rank.three, '4': Rank.four, '5': Rank.five,
        '6': Rank.six, '7': Rank.seven, '8': Rank.eight, '9': Rank.nine,
        '10': Rank.ten, 'J': Rank.jack, 'Q': Rank.queen, 'K': Rank.king, 'A': Rank.ace
    }
    
    # Convert suit string to Suit enum
    suit_map = {
        'H': Suit.hearts, 'D': Suit.diamonds, 'C': Suit.clubs, 'S': Suit.spades
    }
    
    if rank_str not in rank_map:
        raise ValueError(f"Invalid rank: {rank_str}")
    if suit_str not in suit_map:
        raise ValueError(f"Invalid suit: {suit_str}")
    
    return Card(rank=rank_map[rank_str], suit=suit_map[suit_str])

def hand_to_string(hand: Hand) -> str:
    """
    Convert a Hand object to JSON string for database storage.
    
    Args:
        hand: Hand object to convert
        
    Returns:
        str: JSON string representation of the hand
    """
    cards = [card_to_string(card) for card in hand.cards]
    return json.dumps(cards)

def string_to_hand(hand_str: str) -> Hand:
    """
    Convert a JSON string back to a Hand object.
    
    Args:
        hand_str: JSON string representation of the hand
        
    Returns:
        Hand: Hand object
    """
    try:
        card_strings = json.loads(hand_str)
        cards = [string_to_card(card_str) for card_str in card_strings]
        return Hand(cards=cards)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Invalid hand string format: {hand_str}") from e

def hand_to_dict(hand: Hand) -> Dict[str, Any]:
    """
    Convert a Hand object to a dictionary for easy serialization.
    
    Args:
        hand: Hand object to convert
        
    Returns:
        Dict: Dictionary representation of the hand
    """
    return {
        "cards": [card_to_string(card) for card in hand.cards],
        "total": hand.total if hasattr(hand, 'total') else None,
        "is_soft": hand.is_soft if hasattr(hand, 'is_soft') else None,
        "is_blackjack": hand.is_blackjack if hasattr(hand, 'is_blackjack') else None,
        "is_bust": hand.is_bust if hasattr(hand, 'is_bust') else None
    }

def dict_to_hand(hand_dict: Dict[str, Any]) -> Hand:
    """
    Convert a dictionary back to a Hand object.
    
    Args:
        hand_dict: Dictionary representation of the hand
        
    Returns:
        Hand: Hand object
    """
    card_strings = hand_dict.get("cards", [])
    cards = [string_to_card(card_str) for card_str in card_strings]
    return Hand(cards=cards) 