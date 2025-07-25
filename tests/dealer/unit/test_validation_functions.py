import pytest
from dealer_agent.tools.dealer import (
    _validate_initial_hands_dealt,
    _validate_player_turn_ready,
    _validate_dealer_turn_ready,
    _validate_settlement_ready,
    _validate_game_state_consistency,
    GameState,
    GameStateValidationError,
    shuffleShoe,
    Card,
    Suit,
    Rank,
    Hand,
    reset_game_state
)


class TestValidationFunctions:
    """Test the validation helper functions."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_validate_initial_hands_dealt_valid(self):
        """
        Test that _validate_initial_hands_dealt returns True when both hands have 2+ cards.
        Expected result: True
        Mock values: Player and dealer with 2 cards each.
        Why: Verify validation correctly identifies properly dealt hands.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ])
        )
        
        assert _validate_initial_hands_dealt(state) is True
    
    def test_validate_initial_hands_dealt_empty_player_hand(self):
        """
        Test that _validate_initial_hands_dealt returns False when player has no cards.
        Expected result: False
        Mock values: Empty player hand, dealer with 2 cards.
        Why: Verify validation catches incomplete dealing.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ])
        )
        
        assert _validate_initial_hands_dealt(state) is False
    
    def test_validate_initial_hands_dealt_empty_dealer_hand(self):
        """
        Test that _validate_initial_hands_dealt returns False when dealer has no cards.
        Expected result: False
        Mock values: Player with 2 cards, empty dealer hand.
        Why: Verify validation catches incomplete dealing.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[])
        )
        
        assert _validate_initial_hands_dealt(state) is False
    
    def test_validate_initial_hands_dealt_one_card_each(self):
        """
        Test that _validate_initial_hands_dealt returns False when each hand has only 1 card.
        Expected result: False
        Mock values: Player and dealer with 1 card each.
        Why: Verify validation requires at least 2 cards for proper dealing.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace)
            ])
        )
        
        assert _validate_initial_hands_dealt(state) is False
    
    def test_validate_player_turn_ready_valid(self):
        """
        Test that _validate_player_turn_ready returns True for a valid game state.
        Expected result: True
        Mock values: Proper hands dealt, bet placed, player not bust.
        Why: Verify validation correctly identifies when player can act.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        
        assert _validate_player_turn_ready(state) is True
    
    def test_validate_player_turn_ready_no_bet(self):
        """
        Test that _validate_player_turn_ready returns False when no bet is placed.
        Expected result: False
        Mock values: Proper hands dealt but bet is 0.
        Why: Verify validation requires bet before player actions.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=0.0
        )
        
        assert _validate_player_turn_ready(state) is False
    
    def test_validate_player_turn_ready_player_bust(self):
        """
        Test that _validate_player_turn_ready returns False when player is bust.
        Expected result: False
        Mock values: Player with bust hand (22), bet placed.
        Why: Verify validation prevents actions after bust.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.diamonds, rank=Rank.five)  # 10 + 10 + 5 = 25 (bust)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        
        assert _validate_player_turn_ready(state) is False
    
    def test_validate_dealer_turn_ready_player_bust(self):
        """
        Test that _validate_dealer_turn_ready returns True when player is bust.
        Expected result: True
        Mock values: Player bust, hands dealt properly.
        Why: Verify dealer can play when player busts.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.diamonds, rank=Rank.five)  # 10 + 10 + 5 = 25 (bust)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ])
        )
        
        assert _validate_dealer_turn_ready(state) is True
    
    def test_validate_dealer_turn_ready_player_stood(self):
        """
        Test that _validate_dealer_turn_ready returns True when player has stood.
        Expected result: True
        Mock values: Player with 2 cards (stood), dealer with 2 cards.
        Why: Verify dealer can play after player stands.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.nine)  # 19 - player would stand
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.six)
            ])
        )
        
        assert _validate_dealer_turn_ready(state) is True
    
    def test_validate_settlement_ready_player_bust(self):
        """
        Test that _validate_settlement_ready returns True when player is bust.
        Expected result: True
        Mock values: Player bust, bet placed, hands dealt.
        Why: Verify settlement can occur immediately when player busts.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.diamonds, rank=Rank.five)  # 25 (bust)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        
        assert _validate_settlement_ready(state) is True
    
    def test_validate_settlement_ready_both_played(self):
        """
        Test that _validate_settlement_ready returns True when both have completed play.
        Expected result: True
        Mock values: Player stood, dealer played to 17+.
        Why: Verify settlement can occur after both complete.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.nine)  # 19 - stood
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.six),
                Card(suit=Suit.hearts, rank=Rank.two)  # 19 - dealer finished
            ]),
            bet=100.0
        )
        
        assert _validate_settlement_ready(state) is True
    
    def test_validate_settlement_ready_dealer_not_finished(self):
        """
        Test that _validate_settlement_ready returns False when dealer hasn't finished.
        Expected result: False
        Mock values: Player stood, dealer only has 16.
        Why: Verify settlement requires dealer to complete play.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.nine)  # 19 - stood
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.six)  # 16 - must hit
            ]),
            bet=100.0
        )
        
        assert _validate_settlement_ready(state) is False
    
    def test_validate_game_state_consistency_valid(self):
        """
        Test that _validate_game_state_consistency returns True for valid state.
        Expected result: (True, "Game state is consistent")
        Mock values: Fresh game state with proper card counts.
        Why: Verify consistency check passes for valid states.
        """
        state = GameState(shoe=shuffleShoe())  # Fresh state should be valid
        
        is_valid, message = _validate_game_state_consistency(state)
        assert is_valid is True
        assert "consistent" in message.lower()
    
    def test_validate_game_state_consistency_invalid_shoe_count(self):
        """
        Test that _validate_game_state_consistency catches invalid shoe counts.
        Expected result: (False, error message about shoe count)
        Mock values: State with impossible shoe count.
        Why: Verify consistency check catches data corruption.
        """
        state = GameState(
            shoe=[],  # Empty list, but we'll manually set to impossible count
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ])
        )
        # Artificially create invalid state by manipulating shoe
        state.shoe = [Card(suit=Suit.hearts, rank=Rank.ace)] * 400  # Too many cards
        
        is_valid, message = _validate_game_state_consistency(state)
        assert is_valid is False
        assert "shoe count" in message.lower()
    
    def test_validate_game_state_consistency_card_count_mismatch(self):
        """
        Test that _validate_game_state_consistency catches extreme card count corruption.
        Expected result: (False, error message about card count)
        Mock values: State with way too many total cards.
        Why: Verify consistency check catches obvious card corruption.
        """
        # Create a state with extreme card count corruption
        state = GameState(
            shoe=shuffleShoe(),  # 312 cards in shoe
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five),
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten),
                Card(suit=Suit.hearts, rank=Rank.queen),  # 5 cards
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten),
                Card(suit=Suit.hearts, rank=Rank.nine),
                Card(suit=Suit.spades, rank=Rank.eight),
                Card(suit=Suit.diamonds, rank=Rank.seven),  # 5 cards
            ])
        )
        # Total would be 312 + 10 = 322, which exceeds our threshold of 320
        
        is_valid, message = _validate_game_state_consistency(state)
        assert is_valid is False
        assert "card count corruption" in message.lower() 