"""
This is the module that handles Pinochle game play.
"""

from pinochle import hand
from pinochle.cards.utils import convert_to_svg_names, deal_hands
from pinochle.models import utils


def deal_pinochle(player_ids: list, kitty_len: int = 0, kitty_id: str = None) -> None:
    """
    Deal a deck of Pinochle cards into player's hands and the kitty.

    :param player_ids: [description]
    :type player_ids: list
    :param kitty_len: [description]
    :type kitty_len: int
    :param kitty_id: [description]
    :type kitty_id: str
    """
    print(f"player_ids={player_ids}")
    hand_decks, kitty_deck = deal_hands(players=len(player_ids), kitty_cards=kitty_len)

    if kitty_len > 0 and kitty_id is not None:
        hand.addcards(hand_id=kitty_id, cards=convert_to_svg_names(kitty_deck))
    for index, __ in enumerate(player_ids):
        player_info = utils.query_player(player_ids[index])
        hand_id = str(player_info.hand_id)
        hand.addcards(hand_id=hand_id, cards=convert_to_svg_names(hand_decks[index]))


# NOTE- Hands dealt into the database are using generated UUIDs
# NOT the hand_ids already generated. Need to fix the generation
# routine to take a hand id as an argument.
