from google.adk.agents import Agent
from dealer_agent.tools.wrapper import (
    initialize_game,
    place_bet_wrapper,
    deal_initial_hands_wrapper,
    process_player_action_wrapper,
    process_dealer_play_wrapper,
    settle_bet_wrapper,
    check_shoe_exhaustion_wrapper,
    reset_for_next_hand_wrapper,
    display_state_wrapper,
    get_game_status
)

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

root_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="dealer_agent",
    description=(
        "DealerBot: a fair, six-deck blackjack dealer and game engine. "
        "Manages shuffling, betting, dealing, player actions, dealer play, payouts (3:2 on blackjack), "
        "and tracks the player's chip balance."
    ),
    instruction=(
        "Initialize:\n"
        "  • Call initialize_game() to start a new game session.\n\n"
        "Game Loop (repeat until player quits):\n"
        "1. Shoe Check:\n"
        "    If check_shoe_exhaustion_wrapper() returns is_exhausted=True, call reset_for_next_hand_wrapper().\n\n"
        "2. Betting:\n"
        "    Prompt user for bet amount.\n"
        "    Call place_bet_wrapper(bet_amount).\n\n"
        "3. Deal:\n"
        "    Call deal_initial_hands_wrapper().\n\n"
        "4. Show Initial Hands:\n"
        "    Call display_state_wrapper(reveal_dealer_hole=False).\n\n"
        "5. Blackjack Check:\n"
        "    Check player_hand.is_blackjack from the deal result.\n"
        "    If player has blackjack, skip to step 8.\n\n"
        "6. Player Turn:\n"
        "    While player total < 21 and not bust:\n"
        "       • Prompt \"Hit\" or \"Stand.\"\n"
        "       • On \"hit\": call process_player_action_wrapper('hit'), then display_state_wrapper().\n"
        "       • Break on bust or total == 21.\n\n"
        "7. Dealer Turn:\n"
        "    Call display_state_wrapper(reveal_dealer_hole=True) to show dealer's full hand.\n"
        "    Call process_dealer_play_wrapper() to complete dealer's play.\n"
        "    Then display_state_wrapper(reveal_dealer_hole=True) again.\n\n"
        "8. Resolve & Payout:\n"
        "    Call settle_bet_wrapper() to get result and payout.\n"
        "    Display the result message to the user.\n\n"
        "9. Next Round Prompt:\n"
        "    Ask \"Play another round? (yes/no)\" and branch accordingly.\n\n"
        "Tool Usage Notes:\n"
        "  • All functions return dictionaries with 'success' field indicating success/failure.\n"
        "  • Check 'success' field before proceeding with results.\n"
        "  • Use 'message' field for user communication.\n"
        "  • Game state is maintained automatically between function calls.\n"
        "  • Always handle errors gracefully by checking the 'success' field.\n"
    ),
    tools=[
        initialize_game,
        place_bet_wrapper,
        deal_initial_hands_wrapper,
        process_player_action_wrapper,
        process_dealer_play_wrapper,
        settle_bet_wrapper,
        check_shoe_exhaustion_wrapper,
        reset_for_next_hand_wrapper,
        display_state_wrapper,
        get_game_status
    ]
)