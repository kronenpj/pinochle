#!/usr/bin/env python3

"""
The server and data management interface for the Pinochle game.
"""

import base64
import datetime
import logging
import os
import typing
from collections import OrderedDict

from tornado import escape, ioloop, template, web, websocket

from pinochle import custom_log
from pinochle.datastore import DataStore
from pinochle.log_decorator import log_decorator

CHECKED = " checked"
HAND_UPDATED = "{hand: true}"
LOGIN = "/login"
TRICK_UPDATED = "{trick: true}"

TESTING = bool(
    os.getenv("TESTING", "false").strip("'").lower() == "true"
)  # pragma: no cover

COOKIE_LIFETIME_DAYS = 1

USERNAME_PROMPT_HTML_ = (
    '<html><head><link rel="stylesheet" href="/display.css"></head>'
    '<body><form action="/login" method="post" autofocus="true">'
    'Auth Name: <input type="text" name="name" {}></br>'
    '<input type="submit" value="Next">'
    '</form><a href="/">Cancel</a>'
    "</body></html>"
)

MAIN_HTML = "index.html"

LOG = logging.getLogger(__name__)
if TESTING:  # pragma: no cover
    TALOG = logging.getLogger("tornado.access")  # pragma: no cover
    LOG.error("Setting debug level to DEBUG.")  # pragma: no cover
    LOG.setLevel(logging.DEBUG)  # pragma: no cover
    TALOG.setLevel(logging.DEBUG)  # pragma: no cover
    LOG.error(
        "Tornado access Logging level now: {}".format(TALOG.getEffectiveLevel())
    )  # pragma: no cover
else:
    LOG.setLevel(logging.ERROR)  # pragma: no cover

websockethandler = None  # type: typing.Union[WebSocketHandler,None]
ds = DataStore()

LOG.error("Testing: {}".format(TESTING))


def readfile(filename: str) -> str:
    """
    Simple routine to read a file from the given filename and return a string with the file's contents.
    :param filename:
    :return: String with the contents of the file.
    """
    with open(filename, "rb") as infile:
        collect = infile.read().decode()
    return collect


class BaseHandler(web.RequestHandler):
    def data_received(self, chunk) -> None:
        pass  # pragma: no cover

    def get_current_user(self) -> typing.Union[str, None]:
        """
        Determine if a cookie with the name of 'user' exists and return the contents of user if it does.
        :return: None or a str representing the user name retrieved from the cookie.
        """
        return self.get_user_cookie()

    def get_user_cookie(self) -> typing.Union[str, None]:
        """
        Determine if a cookie with the name of 'user' exists and return the contents if it does.
        :return: None or a str representing the user name retrieved from the cookie.
        """
        try:
            user = self.get_secure_cookie("user").decode()  # type: str
            user = user.strip("'")
            # LOG.debug("User cookie contained '{}'.".format(user))
            return user
        except AttributeError:
            # LOG.debug("User cookie didn't exist.")
            return None  # pragma: no cover

    def get_tempuser_cookie(self) -> typing.Union[str, None]:
        """
        Determine if a cookie with the name of 'tempuser' exists and return the contents if it does.
        :return: None or a str representing the user name retrieved from the cookie.
        """
        try:
            tempuser = self.get_secure_cookie("tempuser").decode()  # type: str
            tempuser = tempuser.strip("'")
            LOG.debug("Tempuser cookie contained '{}'.".format(tempuser))
            return tempuser
        except AttributeError:
            LOG.debug("Tempuser cookie didn't exist.")
            return None  # pragma: no cover

    def get(self) -> None:
        self.set_secure_cookie(
            name="user", value=self.get_user_cookie(), expires_days=COOKIE_LIFETIME_DAYS
        )

    def post(self) -> None:
        self.set_secure_cookie(
            name="user", value=self.get_user_cookie(), expires_days=COOKIE_LIFETIME_DAYS
        )


class LogoutHandler(BaseHandler):
    def get(self) -> None:
        self.clear_all_cookies()
        self.redirect("/")

    def post(self) -> None:
        self.clear_all_cookies()
        self.send_error(status_code=405)


class LoginHandler(BaseHandler):
    def get(self) -> None:
        default_user = ""
        if self.get_current_user() is not None:
            LOG.debug("get_current_user returns {}".format(self.get_current_user()))
            default_user = ' value="{}"'.format(str(self.get_current_user()))
        self.write(USERNAME_PROMPT_HTML_.format(default_user))

    def post(self) -> None:
        # LOG.debug("\nName from form: {0}".format(escape.xhtml_escape(self.get_argument('name'))))
        self.set_secure_cookie(
            name="tempuser", value=escape.xhtml_escape(self.get_argument("name"))
        )
        self.write('<html><meta http-equiv="refresh" content="0;url=/"/></html>')


class NewGameH(BaseHandler):
    def get(self) -> None:
        ds.new_game()
        json = ds.game_info()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json)

    def post(self) -> None:
        self.send_error(status_code=405)


class GameDataH(BaseHandler):
    def get(self) -> None:
        gameid = self.get_query_argument(name="gameid", default=None)
        LOG.error(f"Game ID: {gameid}")
        try:
            json = ds.game_info(gameid)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.write(json)
        except KeyError as e:
            LOG.error(f"Exception: {e}")
            self.send_error(status_code=405)

    def post(self) -> None:
        self.send_error(status_code=405)


class ListGames(BaseHandler):
    def get(self) -> None:
        try:
            json = ds.game_list()
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.write(json)
        except KeyError:
            self.send_error(status_code=405)

    def post(self) -> None:
        self.send_error(status_code=405)


class PlayerDeckDataH(BaseHandler):
    @web.authenticated
    def get(self) -> None:
        user = self.get_current_user()  # UUID probably works best here.
        json = ds.player_hand_json(user)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json)

    def post(self) -> None:
        self.send_error(status_code=405)


class TrickDeckDataH(BaseHandler):
    @web.authenticated
    def get(self) -> None:
        json = ds.trick_deck_json()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json)

    def post(self) -> None:
        self.send_error(status_code=405)


# class NewPrizeHandler(BaseHandler):
#     @web.authenticated
#     def get(self) -> None:
#         super().get()
#         self.write(readfile(NEW_PRIZE_HTML))

#     @web.authenticated
#     def post(self) -> None:
#         super().post()
#         really_new = False
#         uuid = None
#         try:
#             uuid = escape.xhtml_escape(self.get_argument("uuid"))
#         except web.MissingArgumentError as e:  # pragma: no cover
#             LOG.warning("Missing UUID: {}".format(e))
#             really_new = True
#         LOG.debug("UUID: {}".format(repr(uuid)))

#         ticket = escape.xhtml_escape(self.get_argument("ticket"))
#         name = escape.xhtml_escape(self.get_argument("name"))
#         callsign = escape.xhtml_escape(self.get_argument("callsign"))
#         prize_desc = escape.xhtml_escape(self.get_argument("prize_desc"))
#         drawing_type = escape.xhtml_escape(self.get_argument("drawing_type"))

#         claimed = False
#         try:
#             if self.get_argument("claimed") == "on":
#                 claimed = True
#         except web.MissingArgumentError:
#             pass

#         hide = False
#         try:
#             if self.get_argument("hide") == "on":
#                 hide = True
#         except web.MissingArgumentError:
#             pass

#         newprize = Prize(
#             uuid=uuid,
#             ticket=ticket,
#             callsign=callsign,
#             name=name,
#             prize_desc=prize_desc,
#             drawing_type=drawing_type,
#             claimed=claimed,
#             hide=hide,
#         )
#         LOG.debug("Prize: {}".format(newprize))
#         prizelist = ds.retrieve_prize()
#         prizelist.update({newprize.uuid: newprize})
#         ds.store_prize(prizelist)
#         # self.write('<html><meta http-equiv="refresh" content="0;url=/"/></html>')
#         # TODO: Figure out how to make this work during testing.
#         try:
#             websockethandler.write_message(message=PRIZE_UPDATED)
#         except AttributeError:
#             pass
#         if really_new:
#             self.redirect("/newprize")
#         else:
#             self.redirect("/prizeadm")


class WebSocketHandler(websocket.WebSocketHandler):
    def open(self) -> None:
        global websockethandler
        websockethandler = self
        # Instruct client to update - mostly for reconnection case
        self.write_message(message=HAND_UPDATED)
        self.write_message(message=TRICK_UPDATED)
        LOG.debug("Web socket opened.")

    def on_message(self, message) -> None:
        self.write_message("Your message was: " + message)

    def on_close(self) -> None:
        global websockethandler
        websockethandler = None
        LOG.debug("Web socket closed.")


def make_app() -> web.Application:
    COOKIE = os.getenv(
        "COOKIE_SECRET", base64.b64encode(os.urandom(50)).decode("ascii")
    ).strip("'")
    LOG.debug("Cookie: %s", COOKIE)
    settings = {
        "cookie_secret": COOKIE,
        "login_url": LOGIN,
        # TODO: Re-enable XSRF checking.
        # "xsrf_cookies" : True,
        "debug": TESTING,
    }
    return web.Application(
        [
            (r"/", web.RedirectHandler, {"url": "/index.html"}),
            (r"/display", web.RedirectHandler, {"url": "/display.html"}),
            (r"/(.*\.html)", web.StaticFileHandler, {"path": "./"}),
            (r"/(.*\.css)", web.StaticFileHandler, {"path": "./"}),
            (r"/(.*\.js)", web.StaticFileHandler, {"path": "./"}),
            (r"/(.*\.jpg)", web.StaticFileHandler, {"path": "./"}),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/newgame", NewGameH),
            (r"/gamelist", ListGames),
            (r"/gamedata", GameDataH),
            (r"/trickdata", TrickDeckDataH),
            (r"/playerdeck", PlayerDeckDataH),
            (r"/ws", WebSocketHandler),
        ],
        **settings,
    )


if __name__ == "__main__":  # pragma: no cover
    APP = make_app()
    APP.listen(8888)
    ioloop.IOLoop.current().start()
