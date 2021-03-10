"""
A set of helper routines for persistence of data and conversion to JSON.

"""

import logging
import os
import pickle
import typing
from collections import OrderedDict
from copy import deepcopy

import jsonpickle

from pinochle import custom_log, object_helpers
from pinochle.cards.card import PinochleCard
from pinochle.cards.deck import PinochleDeck
from pinochle.cards.stack import PinochleStack
from pinochle.player import Player
from pinochle.team import Team
from pinochle.game import Game

FAULTY_PICKLE_E = "Encountered faulty pickle data. Continuing."
J_GAMEID = "game_id"
J_HANDS = "hands"
J_HAND = "hand"
J_PLAYERS = "players"
J_TEAMS = "teams"

TESTING = False
if os.getenv("TESTING", "false").strip("'").lower() == "true":  # pragma: no cover
    TESTING = True
else:
    TESTING = False


class DataStore:
    """
    Storage for pinochle games. This is not the long-term solution as it'll take up
    far too much memory. This will need to transition into a database once it's working.
    """

    DATA_DIR = None
    __games: typing.Dict[str, typing.Union[Game, None]] = dict()
    __teams: typing.Dict[str, typing.Union[Team, None]] = dict()
    __players: typing.Dict[str, typing.Union[Player, None]] = dict()
    __current: str = ""

    def __init__(self) -> None:
        if self.DATA_DIR is None:  # pragma: no cover
            self.DATA_DIR = os.getenv("DATA_DIR", "/home/app/data").strip("'")

        self.game_file = self.DATA_DIR + "/game.pkl"

        self.log = logging.getLogger(__name__)
        if TESTING:  # pragma: no cover
            self.log.setLevel(logging.DEBUG)  # pragma: no cover
        else:
            self.log.setLevel(logging.ERROR)  # pragma: no cover

    def store_game(self, data) -> None:
        """
        Stores data as a pickle.
        :param data: The game data to be stored.
        :type data: OrderedDict
        :return: None
        """
        pickle.dump(data, open(self.game_file, "wb"))

    def new_game(self, teams: typing.Optional[typing.List[Team]] = None) -> str:
        """
        Setup a team, hands and a game.
        """
        # TODO: These need to be created elsewhere and passed in, later.
        team_names = ["Us", "Them"]
        player_names = ["Paul", "Sandra", "Joe", "Marie"]
        n_teams = len(team_names)
        n_players = len(player_names)
        n_kitty = 4
        # TODO: These need to be created elsewhere and passed in, later.

        # Create teams
        z_b_teams = []
        for i_b_teams in range(n_teams):
            z_b_teams.append(Team(name=team_names[i_b_teams]))

        # Create players.
        z_c_players = []
        for i_c_players in range(n_players):
            z_c_players.append(Player(name=player_names[i_c_players]))

        # Attach players to teams.
        for i_c_players in range(len(z_c_players)):
            z_b_teams[int(i_c_players / 2)].players.append(
                deepcopy(z_c_players[i_c_players])
            )

        # Finally create a new game with the teams defined above.
        # This comes with the first hand defined.
        temp_game = object_helpers.create_new_game(z_b_teams)
        self.__current = temp_game.game_id.hex
        self.__games[self.__current] = temp_game

        # Just for fun, add a new hand to the game.
        object_helpers.append_new_hand_to_game(self.__games[self.__current])

        # Return the UUID of the newly created game.
        return jsonpickle.dumps({J_GAMEID: self.__current})

    def populate_teams(self, game_id: typing.Optional[str] = None):
        """
        Set the class teams variable.
        """
        temp_game = game_id or self.__current
        self.__teams[temp_game] = self.__games[temp_game].teams

    def populate_players(self, game_id: typing.Optional[str] = None):
        """
        Set the class players variable for this game.
        """
        temp_game = game_id or self.__current
        self.__players[temp_game] = []
        for t in self.__games[temp_game].teams:
            for p in t.players:
                self.__players[temp_game].append(p)

    def game_info(self, which: str = None) -> typing.Union[str, None]:
        """
        Returns the current or specified game and conveys it as a JSON string.
        :param which: The UUID of the game to return.
        :return: Information about the game represented in JSON.
        :rtype: str
        """
        LOG = custom_log.get_logger()
        which_game = which or self.__current
        LOG.info(f"Game ID: {which_game}")

        # Assemble the subset of information to be displayed
        tempinfo = dict()
        tempinfo[J_GAMEID] = which_game
        tempinfo[J_HANDS] = []
        for ihand in self.__games[which_game].hands:
            tempinfo[J_HANDS].append(dict())
            tempinfo[J_HANDS][ihand.hand_seq][J_HAND] = ihand.hand_seq
            tempinfo[J_HANDS][ihand.hand_seq][J_TEAMS] = []
            tempinfo[J_HANDS][ihand.hand_seq][J_PLAYERS] = []
            for iteam in ihand.teams:
                tempinfo[J_HANDS][ihand.hand_seq][J_TEAMS].append(iteam.name)
                for iplayer in iteam.players:
                    tempinfo[J_HANDS][ihand.hand_seq][J_PLAYERS].append(iplayer.name)

        output = jsonpickle.dumps(tempinfo)
        LOG.error(f"Data: {output}")
        return output

    def game_list(self) -> typing.Union[typing.List[str], None]:
        """
        Returns the current game and conveys it as a JSON string.
        :return: A player's hand (deck) represented in JSON.
        :rtype: str
        """

        templist = list()
        for item in self.__games:
            templist.append(item)
        output = jsonpickle.dumps(templist)
        return output

    def trick_deck_json(self) -> typing.Union[str, None]:
        """
        Returns the deck that contains cards used in the current trick.
        """
        templist = list()
        output = jsonpickle.dumps(templist)
        return output

    def player_hand_json(self, user: str) -> typing.Union[typing.Any, None]:
        """
        Retrieves the player's hand (deck) and conveys it as a JSON string.
        :param user: UUID of player whose hand to return.
        :return: A player's hand (deck) represented in JSON.
        :rtype: str
        """

        data = OrderedDict()
        try:
            data = pickle.load(open(self.game_file, "rb"))
        except FileNotFoundError:  # pragma: no cover
            pass
        newkeys = OrderedDict()
        for uuid in data:
            self.log.info(data.get(uuid).message)
            try:
                newkeys.update({uuid: data.get(uuid)})
            except TypeError as e:  # pragma: no cover
                self.log.error(FAULTY_PICKLE_E)
                self.log.debug("{}".format(e))
            except ValueError as e:  # pragma: no cover
                self.log.error(FAULTY_PICKLE_E)
                newkeys.update({uuid: data.get(uuid)})
                self.log.debug("{}".format(e))
        result = []
        for ident in sorted(newkeys):
            ann_data = newkeys.get(ident)
            result.append(ann_data)
        output = jsonpickle.dumps(result)
        return output

    # def gen_newkeys(self, data) -> OrderedDict:
    #     newkeys = OrderedDict()
    #     for uuid in data:
    #         # self.log.info(data.get(uuid).ticket)
    #         try:
    #             newkeys.update(
    #                 {
    #                     "|".join(["%s" % str(data.get(uuid).ticket), uuid]): data.get(
    #                         uuid
    #                     )
    #                 }
    #             )
    #         except TypeError as e:  # pragma: no cover
    #             self.log.error(FAULTY_PICKLE_E)
    #             self.log.debug("{}".format(e))
    #         except ValueError as e:  # pragma: no cover
    #             self.log.error(FAULTY_PICKLE_E)
    #             newkeys.update(
    #                 {"|".join(["%s" % data.get(uuid).ticket, uuid]): data.get(uuid)}
    #             )
    #             self.log.debug("{}".format(e))
    #     return newkeys

    # def retrieve_prize(self) -> typing.OrderedDict[str, Prize]:
    #     """
    #     Retrieves the pickle file and reconstitutes it as the stored data.
    #     :return: Prizes in a dictionary
    #     :rtype: OrderedDict
    #     """
    #     data = OrderedDict()
    #     try:
    #         data = pickle.load(open(self.game_file, "rb"))
    #     except ValueError:  # pragma: no cover
    #         pass
    #     except FileNotFoundError:  # pragma: no cover
    #         pass

    #     result = OrderedDict()
    #     newkeys = self.gen_newkeys(data)
    #     for ident in sorted(newkeys):
    #         prize = newkeys.get(ident)
    #         result.update({prize.uuid: prize})
    #     return result

    # def prize_json(self) -> typing.Union[typing.Any, None]:
    #     """
    #     Retrieves the pickle file and reconstitutes it as a JSON string.
    #     :return: A list of prizes represented in JSON.
    #     :rtype: str
    #     """
    #     data = OrderedDict()
    #     try:
    #         data = pickle.load(open(self.game_file, "rb"))
    #     except ValueError:  # pragma: no cover
    #         pass
    #     except FileNotFoundError:  # pragma: no cover
    #         pass

    #     result = []
    #     newkeys = self.gen_newkeys(data)
    #     for ident in sorted(newkeys):
    #         prize = newkeys.get(ident)
    #         result.append(prize)
    #     output = jsonpickle.dumps(result)
    #     return output
