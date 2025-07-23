from typing import List, Tuple, Literal, Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext
import random
from enum import Enum
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# Import services
from services.service_manager import service_manager
from services.card_utils import hand_to_string, string_to_hand

# Custom exceptions
class InsufficientBalanceError(Exception):
    """Raised when user doesn't have enough chips."""
    pass

class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass

class SessionError(Exception):
    """Raised when session operations fail."""
    pass

"""
@LeraningNotes:
- Google's ADK framework only supports JSON-serializable simple data types.
  No custom data types are allowed.

- These wrapper functions convert between simple types (that ADK can parse)
  and the complex types used in dealer.py functions.

- This wrapper functions are only to be used with ADK.

- ADK can read custom data types as returns, but cannot build custom data type parameters for inputs.
"""

# Import models
from dealer_agent.models import Card, Hand, HandEvaluation, Suit, Rank

class GameState(BaseModel):
    shoe: List[Card]
    player_hand: Hand = Field(default_factory=Hand)
    dealer_hand: Hand = Field(default_factory=Hand)
    bet: float = 0.0
    # Note: chips are now managed in database, not in-memory


# ----- Tool Context -----

def get_current_session_state(tool_context: ToolContext) -> str:
    """Get session ID from tool context."""
    return tool_context.state.get("session_id")

def get_current_user_id(tool_context: ToolContext) -> str:
    """Get user ID from tool context."""
    return tool_context.state.get("user_id")

# ----- Game Initialization -----

def initialize_game(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Initialize a new game by creating a shuffled shoe and game state.
    
    Creates a fresh game state with a newly shuffled six-deck shoe.
    User balance is managed in the database, not in-memory.
    
    Use this function when:
    - Starting a brand new game session
    - You want to reset everything and start fresh
    - The current game state is corrupted or invalid
    - You need to initialize the game for the first time
    
    Args:
        tool_context (ToolContext, optional): Tool context for getting user balance.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if initialization was successful
            - message (str): Description of the initialization result
            - remaining_cards (int): Number of cards in the shoe (312)
            - balance (float): Current user balance (if tool_context provided)
            - error (str): Error message if initialization failed
    """
    try:
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        # Get user balance if tool_context provided
        balance = None
        if tool_context:
            user_id = tool_context.state.get("user_id")
            if user_id:
                balance = service_manager.user_manager.get_user_balance(user_id)
        
        return {
            "success": True,
            "message": "Game initialized successfully",
            "remaining_cards": len(state.shoe),
            "balance": balance
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ----- Utility Functions -----

def shuffleShoe() -> List[Card]:
    """
    Initialize or re-shuffle the six-deck shoe.
    
    Creates a standard 52-card deck and duplicates it 6 times to create a shoe
    used in casino blackjack. The shoe is then shuffled using Python's random.shuffle.
    
    Use this function when:
    - Starting a new game session
    - The shoe is running low on cards (below threshold)
    - You need a fresh, randomized deck
    
    Returns:
        List[Card]: A list of 312 cards (6 decks) in random order
        
    Example:
        >>> shoe = shuffleShoe()
        >>> len(shoe)
        312
        >>> isinstance(shoe[0], Card)
        True
    """
    single_deck = [Card(suit=s, rank=r) for s in Suit for r in Rank]
    shoe = single_deck * 6
    random.shuffle(shoe)
    return shoe

def drawCard() -> Dict[str, Any]:
    """
    Draw the top card from the shoe and add it to the player's hand.
    
    Removes the top card from the shoe and adds it to the player's hand.
    This function is useful for manual card drawing or implementing custom
    game logic that requires drawing cards outside of the standard game flow.
    
    Use this function when:
    - You want to manually draw a card for the player
    - Implementing custom game rules that require card drawing
    - Testing card drawing functionality
    - You need to draw cards outside of the standard hit/stand flow
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if card was drawn successfully
            - message (str): Description of the drawn card
            - drawn_card (Dict[str, str]): The card that was drawn with suit and rank
            - player_hand (Dict[str, Any]): Updated player hand information
            - player_bust (bool): True if player hand is now bust
            - player_blackjack (bool): True if player hand is now blackjack
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if drawing failed
            
    Raises:
        IndexError: If the shoe is empty and no cards can be drawn
        
    Example:
        >>> result = drawCard(shoe)
        >>> result["success"]
        True
        >>> "drawn_card" in result
        True
        >>> result["remaining_cards"]
        311  # 312 - 1 card drawn
    """
    try:
        state = get_current_state()
        shoe = state.shoe
        card = shoe.pop()
        state.shoe = shoe
        state.player_hand.cards.append(card)
        set_current_state(state)
        
        player_eval = evaluateHand(state.player_hand)
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        return {
            "success": True,
            "message": f"Drew card: {card.rank.value}{card.suit.value}",
            "drawn_card": _card_to_dict(card),
            "player_hand": _hand_to_dict(state.player_hand),
            "player_bust": player_eval.is_bust,
            "player_blackjack": player_eval.is_blackjack,
            "remaining_cards": len(state.shoe)
        }
    except IndexError:
        return {
            "success": False,
            "error": "Shoe is empty, cannot draw card"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



# ----- Chips Management -----

def placeBet(amount: float, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Deduct bet amount from user balance and set current bet.
    
    Validates that the player has sufficient balance and that the bet amount is positive.
    Deducts the bet amount from the user's balance using atomic database operations.
    
    Use this function when:
    - Player wants to place a bet before a hand begins
    - You need to validate bet amount against available balance
    - Setting up the initial game state for a new hand
    
    Args:
        amount (float): The amount to bet, must be positive and <= available balance
        tool_context (ToolContext): Tool context containing user_id and session_id
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if bet was placed successfully
            - message (str): Description of the bet placement result
            - bet (float): The current bet amount
            - balance (float): Updated user balance after bet placement
            - error (str): Error message if bet placement failed
            
    Raises:
        InsufficientBalanceError: If user doesn't have enough balance
        DatabaseError: If database operations fail
    """
    try:
        # Get user_id from tool context
        user_id = tool_context.state.get("user_id")
        if not user_id:
            raise SessionError("User ID not found in session context")
        
        # Validate bet amount
        if amount <= 0:
            raise ValueError("Bet amount must be positive.")
        if amount % 5 != 0:
            raise ValueError("Bet amount must be a multiple of 5.")
        
        # Atomic debit operation - PostgreSQL handles concurrency and validation
        if not service_manager.user_manager.debit_user_balance(user_id, amount):
            raise InsufficientBalanceError("Insufficient balance for bet")
        
        # Update game state
        state = get_current_state()
        state.bet = amount
        set_current_state(state)
        
        # Get updated balance after bet placement
        updated_balance = service_manager.user_manager.get_user_balance(user_id)
        
        return {
            "success": True,
            "message": f"Bet of ${amount} placed successfully",
            "bet": state.bet,
            "balance": updated_balance
        }
    except InsufficientBalanceError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except DatabaseError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}"
        }
    except SessionError as e:
        return {
            "success": False,
            "error": f"Session error: {str(e)}"
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }



# ----- Evaluation -----

def evaluateHand(hand: Hand) -> HandEvaluation:
    """
    Compute best total <=21, detect soft total, blackjack, or bust.
    
    Evaluates a blackjack hand by calculating the optimal total (treating aces as 11
    when beneficial, otherwise as 1), and determining special conditions like
    blackjack (21 with exactly 2 cards), soft totals (containing an ace counted as 11),
    and bust (total > 21).
    
    Use this function when:
    - Determining if a hand is bust
    - Checking for blackjack
    - Calculating hand totals for comparison
    - Determining if a hand is soft (for dealer play decisions)
    - Any time you need to evaluate the strength of a hand
    
    Args:
        hand (Hand): The hand to evaluate, containing a list of cards
        
    Returns:
        HandEvaluation: An object containing:
            - total (int): The best possible total <= 21
            - is_soft (bool): True if hand contains an ace counted as 11
            - is_blackjack (bool): True if hand is exactly 21 with 2 cards
            - is_bust (bool): True if hand total exceeds 21
            
    Example:
        >>> hand = Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace), 
        ...                   Card(suit=Suit.spades, rank=Rank.king)])
        >>> eval = evaluateHand(hand)
        >>> eval.total
        21
        >>> eval.is_blackjack
        True
        >>> eval.is_soft
        True
        >>> eval.is_bust
        False
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

def dealInitialHands() -> Dict[str, Any]:
    """
    Deal two cards each to player and dealer after bet placed.
    
    Deals the initial two cards to both the player and dealer, alternating between
    them (player first, then dealer, then player, then dealer). This simulates
    the standard blackjack dealing procedure.
    
    Use this function when:
    - Starting a new hand after a bet has been placed
    - You need to deal the initial two cards to both players
    - Setting up the game state for player decisions
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if hands were dealt successfully
            - message (str): Description of the dealing result
            - player_hand (Dict[str, Any]): Player's two-card hand
            - dealer_up_card (Dict[str, str]): Dealer's visible up card
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if dealing failed
            
    Example:
        >>> result = dealInitialHands()
        >>> result["success"]
        True
        >>> len(result["player_hand"]["cards"])
        2
        >>> "dealer_up_card" in result
        True
        >>> result["remaining_cards"]
        308  # 312 - 4 cards dealt
    """
    try:
        state = get_current_state()
        for _ in range(2):
            # Draw card for player
            result = drawCard()
            if not result["success"]:
                return result
            state = get_current_state()
            
            # Draw card for dealer
            card = state.shoe.pop()
            state.dealer_hand.cards.append(card)
            set_current_state(state)
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        return {
            "success": True,
            "message": "Initial hands dealt",
            "player_hand": _hand_to_dict(state.player_hand),
            "dealer_up_card": _card_to_dict(state.dealer_hand.cards[0]),
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ----- Player Actions -----

def processPlayerAction(action: Literal['hit', 'stand']) -> Dict[str, Any]:
    """
    Handle player action: hit or stand.
    
    Processes the player's decision to either hit (draw another card) or stand
    (keep current hand). If the player hits, a card is drawn from the shoe and
    added to their hand. If they stand, no action is taken.
    
    Use this function when:
    - Player chooses to hit (draw another card)
    - Player chooses to stand (end their turn)
    - Processing player decisions during their turn
    - Implementing the player action phase of the game
    
    Args:
        action (Literal['hit', 'stand']): The player's chosen action
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if action was processed successfully
            - message (str): Description of the action taken
            - player_hand (Dict[str, Any]): Updated player hand information
            - player_bust (bool): True if player hand is now bust
            - player_blackjack (bool): True if player hand is now blackjack
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if action processing failed
            
    Example:
        >>> result = processPlayerAction("hit")
        >>> result["success"]
        True
        >>> result["message"]
        "Player chose to hit"
        >>> len(result["player_hand"]["cards"])
        3  # 2 initial + 1 hit
    """
    try:
        if action.lower() not in ["hit", "stand"]:
            return {
                "success": False,
                "error": "Action must be 'hit' or 'stand'"
            }
        
        state = get_current_state()
        
        if action.lower() == 'hit':
            result = drawCard()
            if not result["success"]:
                return result
            state = get_current_state()
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        player_eval = evaluateHand(state.player_hand)
        
        return {
            "success": True,
            "message": f"Player chose to {action.lower()}",
            "player_hand": _hand_to_dict(state.player_hand),
            "player_bust": player_eval.is_bust,
            "player_blackjack": player_eval.is_blackjack,
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ----- Dealer Play -----

def processDealerPlay() -> Dict[str, Any]:
    """
    Dealer draws until total >=17 (stand on soft 17).
    
    Implements the dealer's play strategy according to standard casino rules:
    the dealer must hit on totals of 16 or less and stand on 17 or higher,
    including soft 17s (hands containing an ace counted as 11 that total 17).
    
    Use this function when:
    - Player has finished their turn (stood or busted)
    - You need to implement the dealer's automatic play
    - Determining the final dealer hand for settlement
    - After player actions are complete and before settling the bet
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if dealer play was completed successfully
            - message (str): Description of the dealer play result
            - dealer_hand (Dict[str, Any]): Dealer's final hand information
            - dealer_bust (bool): True if dealer hand is bust
            - dealer_blackjack (bool): True if dealer hand is blackjack
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if dealer play failed
            
    Example:
        >>> result = processDealerPlay()
        >>> result["success"]
        True
        >>> result["message"]
        "Dealer play completed"
        >>> result["dealer_hand"]["total"] >= 17
        True  # Dealer stands on 17 or higher
    """
    try:
        state = get_current_state()
        eval = evaluateHand(state.dealer_hand)
        while eval.total < 17:
            card = state.shoe.pop()
            state.dealer_hand.cards.append(card)
            eval = evaluateHand(state.dealer_hand)
        set_current_state(state)
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        dealer_eval = evaluateHand(state.dealer_hand)
        
        return {
            "success": True,
            "message": "Dealer play completed",
            "dealer_hand": _hand_to_dict(state.dealer_hand),
            "dealer_bust": dealer_eval.is_bust,
            "dealer_blackjack": dealer_eval.is_blackjack,
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ----- Settlement -----

def settleBet(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Compare hands, compute payout, update user balance, save round data, and complete session.
    
    Compares the player's and dealer's final hands to determine the outcome
    and calculate the payout. Handles all blackjack rules including bust,
    blackjack payouts (1.5x), and pushes (ties). Updates the user's balance
    using atomic database operations and saves round data to database.
    
    Use this function when:
    - Both player and dealer have completed their hands
    - You need to determine the winner and payout
    - You want to complete the hand and prepare for the next round
    - This is the final step of a hand
    
    Args:
        tool_context (ToolContext): Tool context containing user_id and session_id
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if bet settlement was successful
            - result (str): The outcome: "win", "loss", or "push"
            - payout (float): The payout amount (positive for wins, negative for losses, 0 for push)
            - balance (float): Updated user balance after settlement
            - message (str): Human-readable description of the result
            - round_saved (bool): True if round was saved to database
            - session_completed (bool): True if session was marked as completed
            - total_rounds (int): User's lifetime total number of rounds played
            - reshuffled (bool): True if shoe was reshuffled (always False for now)
            - error (str): Error message if settlement failed
            
    Raises:
        DatabaseError: If database operations fail
        SessionError: If session operations fail
    """
    try:
        # Get user_id and session_id from tool context
        user_id = tool_context.state.get("user_id")
        session_id = tool_context.state.get("session_id")
        
        if not user_id or not session_id:
            raise SessionError("User ID or Session ID not found in session context")
        
        # Get current game state
        state = get_current_state()
        player_eval = evaluateHand(state.player_hand)
        dealer_eval = evaluateHand(state.dealer_hand)
        bet = state.bet
        
        # Get user's current balance before settlement
        chips_before = service_manager.user_manager.get_user_balance(user_id)
        
        # Determine payout and result
        if player_eval.is_bust:
            payout, result = 0.0, 'loss'  # Bet already deducted, no additional loss
        elif dealer_eval.is_bust:
            payout, result = bet * 2, 'win'  # Get bet back + equal winnings
        elif player_eval.is_blackjack and not dealer_eval.is_blackjack:
            payout, result = bet * 2.5, 'win'  # Get bet back + 1.5x winnings
        elif dealer_eval.is_blackjack and not player_eval.is_blackjack:
            payout, result = 0.0, 'loss'  # Bet already deducted, no additional loss
        elif player_eval.total > dealer_eval.total:
            payout, result = bet * 2, 'win'  # Get bet back + equal winnings
        elif player_eval.total < dealer_eval.total:
            payout, result = 0.0, 'loss'  # Bet already deducted, no additional loss
        else:
            payout, result = bet, 'push'  # Get bet back
        
        # Atomic credit operation - PostgreSQL handles concurrency
        # Only credit if payout is positive (wins and pushes)
        if payout > 0:
            if not service_manager.user_manager.credit_user_balance(user_id, payout):
                raise DatabaseError("Failed to credit user balance")
        
        # Get updated balance
        chips_after = service_manager.user_manager.get_user_balance(user_id)
        
        # Get total rounds for this user (lifetime total)
        # For now, we'll use a simple approach - just increment from 1
        # TODO: Implement proper round counting when the database schema supports it
        total_rounds = 1  # This is the first round for this session
        
        # Save round data to database
        round_data = {
            'round_id': str(uuid.uuid4()),
            'session_id': session_id,
            'total_rounds': total_rounds,  # This is the user's lifetime round number
            'bet_amount': bet,
            'player_hand': hand_to_string(state.player_hand),
            'dealer_hand': hand_to_string(state.dealer_hand),
            'player_total': player_eval.total,
            'dealer_total': dealer_eval.total,
            'outcome': result,
            'payout': payout,
            'chips_before': chips_before,
            'chips_after': chips_after
        }
        
        round_saved = service_manager.db_service.save_round(round_data)
        if not round_saved:
            raise DatabaseError("Failed to save round data")
        
        # Mark session as completed
        session_completed = service_manager.db_service.update_session_status(session_id, 'completed')
        if not session_completed:
            raise SessionError("Failed to complete session")
        
        # Clear game state for next round
        state.player_hand = Hand()
        state.dealer_hand = Hand()
        state.bet = 0.0
        set_current_state(state)
        
        return {
            "success": True,
            "result": result,
            "payout": payout,
            "balance": chips_after,
            "message": f"You {result}: ${payout}. Balance now: ${chips_after}",
            "round_saved": round_saved,
            "session_completed": session_completed,
            "total_rounds": total_rounds,  # User's lifetime total rounds
            "reshuffled": False  # Could be enhanced to check shoe exhaustion
        }
    except DatabaseError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}"
        }
    except SessionError as e:
        return {
            "success": False,
            "error": f"Session error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

# ----- Shoe Check & Reset -----

def checkShoeExhaustion(threshold: int = 50) -> Dict[str, Any]:
    """
    Return True if shoe has fewer than threshold cards.
    
    Checks if the shoe is running low on cards and needs to be reshuffled.
    The default threshold of 20 cards is a common casino practice to ensure
    there are enough cards for at least one more complete hand.
    
    Use this function when:
    - After completing a hand
    - Before starting a new hand
    - You need to determine if reshuffling is necessary
    - Implementing shoe management logic
    
    Args:
        threshold (int, optional): Minimum number of cards required in shoe. Defaults to 20.
        
    Returns:
        bool: True if shoe has fewer cards than threshold, False otherwise
        
    Example:
        >>> checkShoeExhaustion()
        False
        >>> checkShoeExhaustion(threshold=10)
        False
    """
    state = get_current_state()
    is_exhausted = len(state.shoe) < threshold

    return {
        "success": True,
        "is_exhausted": is_exhausted,
        "remaining_cards": len(state.shoe),
        "threshold": threshold,
        "message": f"Shoe has {len(state.shoe)} cards remaining (threshold: {threshold})"
    }


def resetForNextHand() -> Dict[str, Any]:
    """
    Prepare for next hand: store round in history, reshuffle if needed, clear hands, reset bet.
    
    Prepares the game state for a new hand by storing the completed round in history,
    clearing the current hands, resetting the bet to zero, and reshuffling the shoe if
    it's running low on cards. This function should be called after settling a bet and
    before the player places their next bet.
    
    Use this function when:
    - After settling a bet and before starting a new hand
    - You need to clean up the game state for the next round
    - Implementing the hand transition logic
    - Ensuring the shoe is properly maintained
    - Recording completed rounds for tracking and analytics
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if reset was completed successfully
            - message (str): Description of the reset result
            - chips (float): Current chip balance (unchanged)
            - remaining_cards (int): Number of cards in the shoe after potential reshuffle
            - reshuffled (bool): True if the shoe was reshuffled due to low card count
            - round_recorded (bool): True if a round was recorded in history
            - total_rounds (int): Total number of rounds played so far
            - error (str): Error message if reset failed
            
    Example:
        >>> result = resetForNextHand()
        >>> result["success"]
        True
        >>> result["message"]
        "Game reset for next hand"
        >>> result["reshuffled"]  # True if shoe was reshuffled
        False
        >>> result["total_rounds"]
        1  # Number of rounds recorded in history
    """
    try:
        state = get_current_state()
        
        # Check if a round was recorded (hands existed before reset)
        round_recorded = bool(state.player_hand.cards or state.dealer_hand.cards)
        
        # Reshuffle if needed
        reshuffled = False
        shoe_check = checkShoeExhaustion()
        if shoe_check["is_exhausted"]:
            state.shoe = shuffleShoe()
            reshuffled = True
        
        # Clear hands and reset bet
        state.player_hand = Hand()
        state.dealer_hand = Hand()
        state.bet = 0.0
        set_current_state(state)
        
        return {
            "success": True,
            "message": "Game reset for next hand",
            "remaining_cards": len(state.shoe),
            "reshuffled": reshuffled,
            "round_recorded": round_recorded,
            "total_rounds": 0  # History is now managed in database
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ----- Display -----

def displayState(revealDealerHole: bool = False, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get a displayable representation of the current game state.
    
    Creates a formatted string representation of the current game state,
    showing player and dealer hands, totals, and user balance. The dealer's
    hole card can be optionally revealed for debugging or end-of-hand display.
    
    Use this function when:
    - Displaying the current game state to the player
    - Debugging game logic
    - Logging game progress
    - Creating user interface displays
    - Showing final hands after dealer play is complete
    - Getting a snapshot of the current game state
    
    Args:
        revealDealerHole (bool, optional): Whether to show dealer's hole card. 
                                          Defaults to False.
        tool_context (ToolContext, optional): Tool context for getting user balance.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if display was generated successfully
            - display_text (str): Formatted string showing the game state
            - player_hand (Dict[str, Any]): Player hand information
            - dealer_hand (Dict[str, Any]): Dealer hand information (if revealed)
            - dealer_up_card (Dict[str, str]): Dealer's visible up card
            - balance (float): Current user balance (if tool_context provided)
            - bet (float): Current bet amount
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if display generation failed
    """
    try:
        state = get_current_state()
        
        # Get user balance if tool_context provided
        balance = None
        if tool_context:
            user_id = tool_context.state.get("user_id")
            if user_id:
                balance = service_manager.user_manager.get_user_balance(user_id)
        
        # Handle case where dealer hand might be empty
        if not state.dealer_hand.cards:
            balance_text = f" | Balance: ${balance}" if balance is not None else ""
            player_hand_str = hand_to_string(state.player_hand)
            display_text = f"Player Hand: {player_hand_str} (Total: {evaluateHand(state.player_hand).total}){balance_text}\nDealer Hand: No cards yet"
        else:
            p_eval = evaluateHand(state.player_hand)
            balance_text = f" | Balance: ${balance}" if balance is not None else ""
            player_hand_str = hand_to_string(state.player_hand)
            lines = [f"Player Hand: {player_hand_str} (Total: {p_eval.total}){balance_text}"]
            if revealDealerHole:
                d_eval = evaluateHand(state.dealer_hand)
                dealer_hand_str = hand_to_string(state.dealer_hand)
                lines.append(f"Dealer Hand: {dealer_hand_str} (Total: {d_eval.total})")
            else:
                up = state.dealer_hand.cards[0]
                up_card_str = hand_to_string(Hand(cards=[up]))
                lines.append(f"Dealer Up-Card: {up_card_str}")
            display_text = '\n'.join(lines)
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        return {
            "success": True,
            "display_text": display_text,
            "player_hand": _hand_to_dict(state.player_hand),
            "dealer_hand": _hand_to_dict(state.dealer_hand) if revealDealerHole else None,
            "dealer_up_card": _card_to_dict(state.dealer_hand.cards[0]) if state.dealer_hand.cards and len(state.dealer_hand.cards) > 0 else None,
            "balance": balance,
            "bet": state.bet,
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



def getGameStatus(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Get the current game status without taking any action.
    
    Retrieves the current state of the game without modifying anything.
    This function is useful for getting a snapshot of the current game
    state for display, logging, or debugging purposes.
    
    Use this function when:
    - You need to check the current game state without taking action
    - Displaying game information to the player
    - Logging game state for debugging
    - Getting a snapshot of the current game
    - Checking if a game is in progress
    
    Args:
        tool_context (ToolContext, optional): Tool context for getting user balance.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if status was retrieved successfully
            - game_state (Dict[str, Any]): Complete game state information
            - message (str): Description of the status retrieval
            - error (str): Error message if status retrieval failed
    """
    try:
        state = get_current_state()
        
        # Get user balance if tool_context provided
        balance = None
        if tool_context:
            user_id = tool_context.state.get("user_id")
            if user_id:
                balance = service_manager.user_manager.get_user_balance(user_id)
        
        # Convert to dict format for agent consumption
        def _card_to_dict(card: Card) -> Dict[str, str]:
            return {"suit": card.suit.value, "rank": card.rank.value}
        
        def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
            return {
                "cards": [_card_to_dict(card) for card in hand.cards],
                "total": evaluateHand(hand).total,
                "is_soft": evaluateHand(hand).is_soft,
                "is_blackjack": evaluateHand(hand).is_blackjack,
                "is_bust": evaluateHand(hand).is_bust
            }
        
        def _state_to_dict(state: GameState) -> Dict[str, Any]:
            return {
                "player_hand": _hand_to_dict(state.player_hand),
                "dealer_hand": _hand_to_dict(state.dealer_hand),
                "bet": state.bet,
                "balance": balance,
                "remaining_cards": len(state.shoe)
            }
        
        return {
            "success": True,
            "game_state": _state_to_dict(state),
            "message": "Current game status retrieved"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def getGameHistory(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the complete game history of all played rounds for the user.
    
    Retrieves the history of all completed rounds from the database for the current user.
    This includes detailed information about each round including hands, bets,
    outcomes, and balance changes. Useful for analytics, debugging, and providing
    game statistics to players.
    
    Use this function when:
    - Displaying game statistics to the player
    - Analyzing game performance and patterns
    - Debugging game flow issues
    - Providing round-by-round summaries
    - Calculating win/loss ratios and other metrics
    
    Args:
        tool_context (ToolContext): Tool context containing user_id
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if history was retrieved successfully
            - total_rounds (int): Total number of rounds played
            - history (List[Dict]): List of round data with detailed information
            - statistics (Dict): Summary statistics including wins, losses, pushes
            - message (str): Description of the history retrieval
            - error (str): Error message if history retrieval failed
    """
    try:
        # Get user_id from tool context
        user_id = tool_context.state.get("user_id")
        if not user_id:
            raise SessionError("User ID not found in session context")
        
        # Get user's current balance
        current_balance = service_manager.user_manager.get_user_balance(user_id)
        
        # For now, return empty history since database round tracking is not yet implemented
        # TODO: Implement proper round tracking in database
        rounds = []
        
        # Calculate statistics
        wins = 0
        losses = 0
        pushes = 0
        total_bet = 0.0
        net_profit = current_balance - 100.0  # Assuming starting balance of 100
        
        statistics = {
            "total_rounds": len(rounds),
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": 0.0,
            "total_bet": total_bet,
            "net_profit": net_profit,
            "current_balance": current_balance
        }
        
        return {
            "success": True,
            "total_rounds": len(rounds),
            "history": rounds,
            "statistics": statistics,
            "message": f"Retrieved history of {len(rounds)} rounds"
        }
    except DatabaseError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}"
        }
    except SessionError as e:
        return {
            "success": False,
            "error": f"Session error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

# Note: I/O functions promptUser and logGame should be implemented in the agent layer.

# ----- State Management -----

# Global state to maintain the game state across function calls
_global_state: Optional[GameState] = None

def get_current_state() -> GameState:
    """
    Get the current global state, creating one if it doesn't exist.
    
    Returns:
        GameState: The current game state
    """
    global _global_state
    if _global_state is None:
        _global_state = GameState(shoe=shuffleShoe())
    return _global_state

def set_current_state(state: GameState) -> None:
    """
    Set the global state.
    
    Args:
        state (GameState): The game state to set
    """
    global _global_state
    _global_state = state

def reset_game_state() -> None:
    """
    Reset the global state to None, forcing a new state to be created.
    """
    global _global_state
    _global_state = None
