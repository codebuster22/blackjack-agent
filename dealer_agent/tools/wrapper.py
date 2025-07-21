"""
@LeraningNotes:
- Google's ADK framework only supports JSON-serializable simple data types.
  No custom data types are allowed.

- These wrapper functions convert between simple types (that ADK can parse)
  and the complex types used in dealer.py functions.

- This wrapper functions are only to be used with ADK.

- ADK can read custom data types as returns, but cannot build custom data type parameters for inputs.
"""

import json
from typing import Dict, Any
from .dealer import (
    shuffleShoe, drawCard, placeBet, updateChips, evaluateHand,
    dealInitialHands, processPlayerAction, processDealerPlay,
    settleBet, checkShoeExhaustion, resetForNextHand, displayState,
    get_current_state, set_current_state, reset_game_state,
    GameState, Card, Hand
)

def _card_to_dict(card: Card) -> Dict[str, str]:
    """Convert a Card object to a simple dictionary."""
    return {"suit": card.suit.value, "rank": card.rank.value}

def _hand_to_dict(hand: Hand) -> Dict[str, Any]:
    """Convert a Hand object to a simple dictionary."""
    return {
        "cards": [_card_to_dict(card) for card in hand.cards],
        "total": evaluateHand(hand).total,
        "is_soft": evaluateHand(hand).is_soft,
        "is_blackjack": evaluateHand(hand).is_blackjack,
        "is_bust": evaluateHand(hand).is_bust
    }

def _state_to_dict(state: GameState) -> Dict[str, Any]:
    """Convert a GameState object to a simple dictionary."""
    return {
        "player_hand": _hand_to_dict(state.player_hand),
        "dealer_hand": _hand_to_dict(state.dealer_hand),
        "bet": state.bet,
        "chips": state.chips,
        "remaining_cards": len(state.shoe)
    }

# Wrapper Functions

def initialize_game() -> Dict[str, Any]:
    """
    Initialize a new game by creating a shuffled shoe and game state.
    
    Creates a fresh game state with a newly shuffled six-deck shoe and
    initializes the player's chip balance to $100. This function should
    be called when starting a completely new game session.
    
    Use this function when:
    - Starting a brand new game session
    - You want to reset everything and start fresh
    - The current game state is corrupted or invalid
    - You need to initialize the game for the first time
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if initialization was successful
            - message (str): Description of the initialization result
            - chips (float): Initial chip balance (100.0)
            - remaining_cards (int): Number of cards in the shoe (312)
            - error (str): Error message if initialization failed
            
    Example:
        >>> result = initialize_game()
        >>> result["success"]
        True
        >>> result["chips"]
        100.0
        >>> result["remaining_cards"]
        312
    """
    try:
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        return {
            "success": True,
            "message": "Game initialized successfully",
            "chips": state.chips,
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def draw_card_wrapper() -> Dict[str, Any]:
    """
    Draw a card from the shoe and add it to the player's hand.
    
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
        >>> result = draw_card_wrapper()
        >>> result["success"]
        True
        >>> "drawn_card" in result
        True
        >>> result["remaining_cards"]
        311  # 312 - 1 card drawn
    """
    try:
        state = get_current_state()
        card, new_shoe = drawCard(state.shoe)
        state.shoe = new_shoe
        state.player_hand.cards.append(card)
        set_current_state(state)
        
        player_eval = evaluateHand(state.player_hand)
        
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

def place_bet_wrapper(bet_amount: float) -> Dict[str, Any]:
    """
    Place a bet using the specified amount.
    
    Deducts the bet amount from the player's chips and sets it as the
    current bet for the hand. Validates that the player has sufficient
    chips and that the bet amount is positive.
    
    Use this function when:
    - Player wants to place a bet before a hand begins
    - You need to validate bet amount against available chips
    - Setting up the initial game state for a new hand
    - Before dealing cards to start a new round
    
    Args:
        bet_amount (float): The amount to bet, must be positive and <= available chips
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if bet was placed successfully
            - message (str): Description of the bet placement result
            - chips (float): Updated chip balance after bet deduction
            - bet (float): The current bet amount
            - error (str): Error message if bet placement failed
            
    Raises:
        ValueError: If bet amount is not positive or exceeds available chips
        
    Example:
        >>> result = place_bet_wrapper(25.0)
        >>> result["success"]
        True
        >>> result["chips"]
        75.0  # 100 - 25
        >>> result["bet"]
        25.0
    """
    try:
        state = get_current_state()
        updated_state = placeBet(state, bet_amount)
        set_current_state(updated_state)
        return {
            "success": True,
            "message": f"Bet of ${bet_amount} placed successfully",
            "chips": updated_state.chips,
            "bet": updated_state.bet
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

def deal_initial_hands_wrapper() -> Dict[str, Any]:
    """
    Deal the initial two cards to both player and dealer.
    
    Deals two cards each to the player and dealer, alternating between
    them (player first, then dealer, then player, then dealer). This
    simulates the standard blackjack dealing procedure.
    
    Use this function when:
    - Starting a new hand after a bet has been placed
    - You need to deal the initial two cards to both players
    - Setting up the game state for player decisions
    - After placing a bet and before player actions
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if hands were dealt successfully
            - message (str): Description of the dealing result
            - player_hand (Dict[str, Any]): Player's two-card hand
            - dealer_up_card (Dict[str, str]): Dealer's visible up card
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if dealing failed
            
    Example:
        >>> result = deal_initial_hands_wrapper()
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
        updated_state = dealInitialHands(state)
        set_current_state(updated_state)
        
        return {
            "success": True,
            "message": "Initial hands dealt",
            "player_hand": _hand_to_dict(updated_state.player_hand),
            "dealer_up_card": _card_to_dict(updated_state.dealer_hand.cards[0]),
            "remaining_cards": len(updated_state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_player_action_wrapper(action: str) -> Dict[str, Any]:
    """
    Process a player action (hit or stand).
    
    Handles the player's decision to either hit (draw another card) or
    stand (keep current hand). If the player hits, a card is drawn from
    the shoe and added to their hand. If they stand, no action is taken.
    
    Use this function when:
    - Player chooses to hit (draw another card)
    - Player chooses to stand (end their turn)
    - Processing player decisions during their turn
    - Implementing the player action phase of the game
    - After dealing initial hands and before dealer play
    
    Args:
        action (str): The player's chosen action, must be "hit" or "stand" (case-insensitive)
        
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
        >>> result = process_player_action_wrapper("hit")
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
        updated_state = processPlayerAction(action.lower(), state)
        set_current_state(updated_state)
        
        player_eval = evaluateHand(updated_state.player_hand)
        
        return {
            "success": True,
            "message": f"Player chose to {action.lower()}",
            "player_hand": _hand_to_dict(updated_state.player_hand),
            "player_bust": player_eval.is_bust,
            "player_blackjack": player_eval.is_blackjack,
            "remaining_cards": len(updated_state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_dealer_play_wrapper() -> Dict[str, Any]:
    """
    Process the dealer's play (draw cards until total >= 17).
    
    Implements the dealer's automatic play strategy according to standard
    casino rules: the dealer must hit on totals of 16 or less and stand
    on 17 or higher, including soft 17s.
    
    Use this function when:
    - Player has finished their turn (stood or busted)
    - You need to implement the dealer's automatic play
    - Determining the final dealer hand for settlement
    - After player actions are complete and before settling the bet
    - When the player has stood or busted
    
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
        >>> result = process_dealer_play_wrapper()
        >>> result["success"]
        True
        >>> result["message"]
        "Dealer play completed"
        >>> result["dealer_hand"]["total"] >= 17
        True  # Dealer stands on 17 or higher
    """
    try:
        state = get_current_state()
        updated_state = processDealerPlay(state)
        set_current_state(updated_state)
        
        dealer_eval = evaluateHand(updated_state.dealer_hand)
        
        return {
            "success": True,
            "message": "Dealer play completed",
            "dealer_hand": _hand_to_dict(updated_state.dealer_hand),
            "dealer_bust": dealer_eval.is_bust,
            "dealer_blackjack": dealer_eval.is_blackjack,
            "remaining_cards": len(updated_state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def settle_bet_wrapper() -> Dict[str, Any]:
    """
    Settle the current bet and determine the outcome.
    
    Compares the player's and dealer's final hands to determine the
    outcome and calculate the payout. Handles all blackjack rules
    including bust, blackjack payouts (1.5x), and pushes (ties).
    Updates the player's chip balance with the payout.
    
    Use this function when:
    - Both player and dealer have completed their hands
    - You need to determine the winner and payout
    - After dealer play is complete
    - To get the result for logging or display purposes
    - Before starting a new hand
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if bet settlement was successful
            - result (str): The outcome: "win", "loss", or "push"
            - payout (float): The payout amount (positive for wins, negative for losses, 0 for push)
            - chips (float): Updated chip balance after payout
            - message (str): Human-readable description of the result
            - error (str): Error message if settlement failed
            
    Example:
        >>> result = settle_bet_wrapper()
        >>> result["success"]
        True
        >>> result["result"] in ["win", "loss", "push"]
        True
        >>> result["payout"]  # Could be positive, negative, or 0
        25.0
    """
    try:
        state = get_current_state()
        payout, result = settleBet(state)
        updated_state = updateChips(state, payout)
        set_current_state(updated_state)
        
        return {
            "success": True,
            "result": result,
            "payout": payout,
            "chips": updated_state.chips,
            "message": f"You {result}: ${payout}. Chips now: ${updated_state.chips}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_shoe_exhaustion_wrapper(threshold: int = 20) -> Dict[str, Any]:
    """
    Check if the shoe needs to be reshuffled.
    
    Checks if the shoe is running low on cards and needs to be reshuffled.
    The default threshold of 20 cards is a common casino practice to ensure
    there are enough cards for at least one more complete hand.
    
    Use this function when:
    - After completing a hand
    - Before starting a new hand
    - You need to determine if reshuffling is necessary
    - Implementing shoe management logic
    - Monitoring shoe depletion
    
    Args:
        threshold (int, optional): Minimum number of cards required in shoe. Defaults to 20.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if check was completed successfully
            - is_exhausted (bool): True if shoe has fewer cards than threshold
            - remaining_cards (int): Number of cards left in the shoe
            - threshold (int): The threshold used for the check
            - message (str): Human-readable description of the shoe status
            - error (str): Error message if check failed
            
    Example:
        >>> result = check_shoe_exhaustion_wrapper()
        >>> result["success"]
        True
        >>> result["is_exhausted"]  # True if cards < 20
        False
        >>> result["remaining_cards"]
        312  # Full shoe
    """
    try:
        state = get_current_state()
        is_exhausted = checkShoeExhaustion(state, threshold)
        
        return {
            "success": True,
            "is_exhausted": is_exhausted,
            "remaining_cards": len(state.shoe),
            "threshold": threshold,
            "message": f"Shoe has {len(state.shoe)} cards remaining (threshold: {threshold})"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def reset_for_next_hand_wrapper() -> Dict[str, Any]:
    """
    Reset the game state for the next hand.
    
    Prepares the game state for a new hand by clearing the current hands,
    resetting the bet to zero, and reshuffling the shoe if it's running low
    on cards. This function should be called after settling a bet and before
    the player places their next bet.
    
    Use this function when:
    - After settling a bet and before starting a new hand
    - You need to clean up the game state for the next round
    - Implementing the hand transition logic
    - Ensuring the shoe is properly maintained
    - Starting a new round after a completed hand
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if reset was completed successfully
            - message (str): Description of the reset result
            - chips (float): Current chip balance (unchanged)
            - remaining_cards (int): Number of cards in the shoe after potential reshuffle
            - reshuffled (bool): True if the shoe was reshuffled due to low card count
            - error (str): Error message if reset failed
            
    Example:
        >>> result = reset_for_next_hand_wrapper()
        >>> result["success"]
        True
        >>> result["message"]
        "Game reset for next hand"
        >>> result["reshuffled"]  # True if shoe was reshuffled
        False
    """
    try:
        state = get_current_state()
        updated_state = resetForNextHand(state)
        set_current_state(updated_state)
        
        return {
            "success": True,
            "message": "Game reset for next hand",
            "chips": updated_state.chips,
            "remaining_cards": len(updated_state.shoe),
            "reshuffled": len(updated_state.shoe) == 312  # Full shoe indicates reshuffle
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def display_state_wrapper(reveal_dealer_hole: bool = False) -> Dict[str, Any]:
    """
    Get a displayable representation of the current game state.
    
    Creates a formatted string representation of the current game state,
    showing player and dealer hands, totals, and chip balance. The dealer's
    hole card can be optionally revealed for debugging or end-of-hand display.
    
    Use this function when:
    - Displaying the current game state to the player
    - Debugging game logic
    - Logging game progress
    - Creating user interface displays
    - Showing final hands after dealer play is complete
    - Getting a snapshot of the current game state
    
    Args:
        reveal_dealer_hole (bool, optional): Whether to show dealer's hole card. 
                                          Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if display was generated successfully
            - display_text (str): Formatted string showing the game state
            - player_hand (Dict[str, Any]): Player hand information
            - dealer_hand (Dict[str, Any]): Dealer hand information (if revealed)
            - dealer_up_card (Dict[str, str]): Dealer's visible up card
            - chips (float): Current chip balance
            - bet (float): Current bet amount
            - remaining_cards (int): Number of cards left in the shoe
            - error (str): Error message if display generation failed
            
    Example:
        >>> result = display_state_wrapper()
        >>> result["success"]
        True
        >>> "Player Hand:" in result["display_text"]
        True
        >>> result["dealer_up_card"] is not None
        True
    """
    try:
        state = get_current_state()
        
        # Handle case where dealer hand might be empty
        if not state.dealer_hand.cards:
            display_text = f"Player Hand: {[f'{c.rank}{c.suit}' for c in state.player_hand.cards]} (Total: {evaluateHand(state.player_hand).total}) | Chips: {state.chips}\nDealer Hand: No cards yet"
        else:
            display_text = displayState(state, reveal_dealer_hole)
        
        return {
            "success": True,
            "display_text": display_text,
            "player_hand": _hand_to_dict(state.player_hand),
            "dealer_hand": _hand_to_dict(state.dealer_hand) if reveal_dealer_hole else None,
            "dealer_up_card": _card_to_dict(state.dealer_hand.cards[0]) if state.dealer_hand.cards and len(state.dealer_hand.cards) > 0 else None,
            "chips": state.chips,
            "bet": state.bet,
            "remaining_cards": len(state.shoe)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_game_status() -> Dict[str, Any]:
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
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if status was retrieved successfully
            - game_state (Dict[str, Any]): Complete game state information
            - message (str): Description of the status retrieval
            - error (str): Error message if status retrieval failed
            
    Example:
        >>> result = get_game_status()
        >>> result["success"]
        True
        >>> "game_state" in result
        True
        >>> result["game_state"]["chips"]
        100.0
    """
    try:
        state = get_current_state()
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