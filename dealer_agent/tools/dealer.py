from typing import List, Tuple, Literal, Optional
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
    chips: float = 100.0  # In-memory chips tracker
    history: List[dict] = Field(default_factory=list)

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

def drawCard(shoe: List[Card]) -> Tuple[Card, List[Card]]:
    """
    Draw the top card from the shoe.
    
    Removes and returns the last card from the shoe (simulating drawing from the top
    of a physical deck). Also returns the updated shoe with the card removed.
    
    Use this function when:
    - Dealing cards to players or dealer
    - Player chooses to hit
    - Dealer needs to draw additional cards
    
    Args:
        shoe (List[Card]): The current shoe containing remaining cards
        
    Returns:
        Tuple[Card, List[Card]]: A tuple containing:
            - Card: The drawn card
            - List[Card]: The updated shoe with the card removed
            
    Raises:
        IndexError: If the shoe is empty
        
    Example:
        >>> shoe = shuffleShoe()
        >>> card, new_shoe = drawCard(shoe)
        >>> len(new_shoe)
        311
        >>> isinstance(card, Card)
        True
    """
    card = shoe.pop()
    return card, shoe

# ----- Chips Management -----

def placeBet(state: GameState, amount: float) -> GameState:
    """
    Deduct bet amount from chips and set current bet.
    
    Validates that the player has sufficient chips and that the bet amount is positive.
    Deducts the bet amount from the player's chips and sets it as the current bet.
    
    Use this function when:
    - Player wants to place a bet before a hand begins
    - You need to validate bet amount against available chips
    - Setting up the initial game state for a new hand
    
    Args:
        state (GameState): The current game state containing chips and bet information
        amount (float): The amount to bet, must be positive and <= available chips
        
    Returns:
        GameState: Updated game state with chips deducted and bet set
        
    Raises:
        ValueError: If bet amount is not positive or exceeds available chips
        
    Example:
        >>> state = GameState(shoe=shuffleShoe(), chips=100.0)
        >>> updated_state = placeBet(state, 25.0)
        >>> updated_state.chips
        75.0
        >>> updated_state.bet
        25.0
    """
    if amount <= 0:
        raise ValueError("Bet amount must be positive.")
    if state.chips < amount:
        raise ValueError("Insufficient chips to place bet.")
    state.chips -= amount
    state.bet = amount
    return state

def updateChips(state: GameState, payout: float) -> GameState:
    """
    Apply payout (positive or negative) to chips.
    
    Adds the payout amount to the player's chips. Positive values represent winnings,
    negative values represent losses. This function is typically called after
    settling a bet to update the player's chip balance.
    
    Use this function when:
    - Settling bets after a hand is complete
    - Adding winnings to player's chips
    - Deducting losses from player's chips
    - Any time you need to modify the player's chip balance
    
    Args:
        state (GameState): The current game state containing chips information
        payout (float): The amount to add to chips (positive for wins, negative for losses)
        
    Returns:
        GameState: Updated game state with modified chip balance
        
    Example:
        >>> state = GameState(shoe=shuffleShoe(), chips=100.0)
        >>> # Player wins $25
        >>> updated_state = updateChips(state, 25.0)
        >>> updated_state.chips
        125.0
        >>> # Player loses $10
        >>> updated_state = updateChips(updated_state, -10.0)
        >>> updated_state.chips
        115.0
    """
    state.chips += payout
    return state

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

def dealInitialHands(state: GameState) -> GameState:
    """
    Deal two cards each to player and dealer after bet placed.
    
    Deals the initial two cards to both the player and dealer, alternating between
    them (player first, then dealer, then player, then dealer). This simulates
    the standard blackjack dealing procedure.
    
    Use this function when:
    - Starting a new hand after a bet has been placed
    - You need to deal the initial two cards to both players
    - Setting up the game state for player decisions
    
    Args:
        state (GameState): The current game state with an active bet and empty hands
        
    Returns:
        GameState: Updated game state with two cards each in player and dealer hands
        
    Example:
        >>> state = GameState(shoe=shuffleShoe(), bet=25.0)
        >>> updated_state = dealInitialHands(state)
        >>> len(updated_state.player_hand.cards)
        2
        >>> len(updated_state.dealer_hand.cards)
        2
        >>> len(updated_state.shoe)
        308  # 312 - 4 cards dealt
    """
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
        state (GameState): The current game state with player and dealer hands
        
    Returns:
        GameState: Updated game state (modified if action was 'hit')
        
    Example:
        >>> state = GameState(shoe=shuffleShoe())
        >>> state.player_hand.cards = [Card(suit=Suit.hearts, rank=Rank.ten),
        ...                            Card(suit=Suit.spades, rank=Rank.six)]
        >>> # Player hits
        >>> updated_state = processPlayerAction('hit', state)
        >>> len(updated_state.player_hand.cards)
        3
        >>> # Player stands
        >>> final_state = processPlayerAction('stand', updated_state)
        >>> len(final_state.player_hand.cards)
        3  # No change
    """
    if action == 'hit':
        card, state.shoe = drawCard(state.shoe)
        state.player_hand.cards.append(card)
    return state

# ----- Dealer Play -----

def processDealerPlay(state: GameState) -> GameState:
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
    
    Args:
        state (GameState): The current game state with dealer's up card and hole card
        
    Returns:
        GameState: Updated game state with dealer's final hand
        
    Example:
        >>> state = GameState(shoe=shuffleShoe())
        >>> state.dealer_hand.cards = [Card(suit=Suit.hearts, rank=Rank.six),
        ...                            Card(suit=Suit.spades, rank=Rank.ten)]
        >>> # Dealer has 16, must hit
        >>> updated_state = processDealerPlay(state)
        >>> eval = evaluateHand(updated_state.dealer_hand)
        >>> eval.total >= 17
        True
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
    Compare hands, compute payout relative to bet, but do not update chips.
    
    Compares the player's and dealer's final hands to determine the outcome
    and calculate the payout. Handles all blackjack rules including bust,
    blackjack payouts (1.5x), and pushes (ties). Returns the payout amount
    and result type without modifying the game state.
    
    Use this function when:
    - Both player and dealer have completed their hands
    - You need to determine the winner and payout
    - Before updating the player's chip balance
    - To get the result for logging or display purposes
    
    Args:
        state (GameState): The current game state with completed player and dealer hands
        
    Returns:
        Tuple[float, Literal['win', 'loss', 'push']]: A tuple containing:
            - float: The payout amount (positive for wins, negative for losses, 0 for push)
            - Literal['win', 'loss', 'push']: The result of the hand
            
    Example:
        >>> state = GameState(bet=25.0)
        >>> # Player blackjack
        >>> state.player_hand.cards = [Card(suit=Suit.hearts, rank=Rank.ace),
        ...                            Card(suit=Suit.spades, rank=Rank.king)]
        >>> state.dealer_hand.cards = [Card(suit=Suit.diamonds, rank=Rank.ten),
        ...                            Card(suit=Suit.clubs, rank=Rank.seven)]
        >>> payout, result = settleBet(state)
        >>> payout
        37.5  # 25 * 1.5 for blackjack
        >>> result
        'win'
    """
    player_eval = evaluateHand(state.player_hand)
    dealer_eval = evaluateHand(state.dealer_hand)
    bet = state.bet
    # Player bust
    if player_eval.is_bust:
        return -bet, 'loss'
    # Dealer bust
    if dealer_eval.is_bust:
        return bet, 'win'
    # Blackjack
    if player_eval.is_blackjack and not dealer_eval.is_blackjack:
        return bet * 1.5, 'win'
    if dealer_eval.is_blackjack and not player_eval.is_blackjack:
        return -bet, 'loss'
    # Compare totals
    if player_eval.total > dealer_eval.total:
        return bet, 'win'
    if player_eval.total < dealer_eval.total:
        return -bet, 'loss'
    return 0.0, 'push'

# ----- Shoe Check & Reset -----

def checkShoeExhaustion(state: GameState, threshold: int = 20) -> bool:
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
        state (GameState): The current game state containing the shoe
        threshold (int, optional): Minimum number of cards required in shoe. Defaults to 20.
        
    Returns:
        bool: True if shoe has fewer cards than threshold, False otherwise
        
    Example:
        >>> state = GameState(shoe=[Card(suit=Suit.hearts, rank=Rank.ace)] * 15)
        >>> checkShoeExhaustion(state)
        True
        >>> checkShoeExhaustion(state, threshold=10)
        False
    """
    return len(state.shoe) < threshold


def resetForNextHand(state: GameState) -> GameState:
    """
    Prepare for next hand: reshuffle if needed, clear hands, reset bet.
    
    Prepares the game state for a new hand by clearing the current hands,
    resetting the bet to zero, and reshuffling the shoe if it's running low
    on cards. This function should be called after settling a bet and before
    the player places their next bet.
    
    Use this function when:
    - After settling a bet and before starting a new hand
    - You need to clean up the game state for the next round
    - Implementing the hand transition logic
    - Ensuring the shoe is properly maintained
    
    Args:
        state (GameState): The current game state after a completed hand
        
    Returns:
        GameState: Updated game state ready for a new hand
        
    Example:
        >>> state = GameState(shoe=[Card(suit=Suit.hearts, rank=Rank.ace)] * 15,
        ...                   bet=25.0)
        >>> state.player_hand.cards = [Card(suit=Suit.hearts, rank=Rank.ten)]
        >>> state.dealer_hand.cards = [Card(suit=Suit.spades, rank=Rank.king)]
        >>> updated_state = resetForNextHand(state)
        >>> len(updated_state.player_hand.cards)
        0
        >>> len(updated_state.dealer_hand.cards)
        0
        >>> updated_state.bet
        0.0
        >>> len(updated_state.shoe)
        312  # Reshuffled due to low card count
    """
    if checkShoeExhaustion(state):
        state.shoe = shuffleShoe()
    state.player_hand = Hand()
    state.dealer_hand = Hand()
    state.bet = 0.0
    return state

# ----- Display -----

def displayState(state: GameState, revealDealerHole: bool = False) -> str:
    """
    Render human-readable game state.
    
    Creates a formatted string representation of the current game state,
    showing player and dealer hands, totals, and chip balance. The dealer's
    hole card can be optionally revealed for debugging or end-of-hand display.
    
    Use this function when:
    - Displaying the current game state to the player
    - Debugging game logic
    - Logging game progress
    - Creating user interface displays
    - Showing final hands after dealer play is complete
    
    Args:
        state (GameState): The current game state to display
        revealDealerHole (bool, optional): Whether to show dealer's hole card. 
                                          Defaults to False.
        
    Returns:
        str: A formatted string showing the game state
        
    Example:
        >>> state = GameState(shoe=shuffleShoe(), chips=100.0)
        >>> state.player_hand.cards = [Card(suit=Suit.hearts, rank=Rank.ten),
        ...                            Card(suit=Suit.spades, rank=Rank.six)]
        >>> state.dealer_hand.cards = [Card(suit=Suit.diamonds, rank=Rank.king),
        ...                            Card(suit=Suit.clubs, rank=Rank.ace)]
        >>> display = displayState(state)
        >>> "Player Hand:" in display
        True
        >>> "Dealer Up-Card:" in display
        True
        >>> "K" in display  # Dealer's up card
        True
        >>> display = displayState(state, revealDealerHole=True)
        >>> "Dealer Hand:" in display
        True
    """
    p_eval = evaluateHand(state.player_hand)
    lines = [f"Player Hand: {[f'{c.rank}{c.suit}' for c in state.player_hand.cards]} (Total: {p_eval.total}) | Chips: {state.chips}"]
    if revealDealerHole:
        d_eval = evaluateHand(state.dealer_hand)
        lines.append(f"Dealer Hand: {[f'{c.rank}{c.suit}' for c in state.dealer_hand.cards]} (Total: {d_eval.total})")
    else:
        up = state.dealer_hand.cards[0]
        lines.append(f"Dealer Up-Card: {up.rank}{up.suit}")
    return '\n'.join(lines)

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
