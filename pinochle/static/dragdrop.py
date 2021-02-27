from browser import document, alert
from browser.timer import set_timeout
import browser.html as html
from random import randrange, choice, shuffle, sample

# from time import time


class Board(html.DIV):
    def __init__(self, boardwidth, boardheight, pattern):
        html.DIV.__init__(
            self,
            "",
            style={
                "position": "absolute",
                "background-color": "#dc8264",
                "border": "{0}px solid #820a0a".format(borderwidth),
            },
        )
        self.boardwidth = boardwidth
        self.boardheight = boardheight
        self.left = innersize * 5
        self.top = 0
        self.width = outersize * boardwidth
        self.height = outersize * boardheight
        self.squaredict = {}
        self.poslist = []
        self.currentpos = None
        for pos in pattern:
            p = Position(pos)
            self.poslist.append(p)
            for square in pos:
                self.squaredict[square] = p
            self <= p


class Position(html.DIV):
    def __init__(self, pos):
        html.DIV.__init__(
            self,
            "",
            style={
                "position": "absolute",
                "border": "{0}px solid #820a0a".format(borderwidth),
                "background-color": "inherit",
            },
        )
        self.orientation = "V" if pos[0][0] == pos[1][0] else "H"
        self.width = innersize if self.orientation == "V" else innersize + outersize
        self.height = innersize + outersize if self.orientation == "V" else innersize
        self.left = outersize * pos[0][0]
        self.top = outersize * pos[0][1]
        self.squares = pos
        self.domino = None


class Dotpattern(html.DIV):
    def __init__(self, n):
        html.DIV.__init__(
            self,
            "",
            style={
                "position": "absolute",
                "height": "80%",
                "width": "40%",
                "background-color": "#1F1F1F",
            },
        )
        if n % 2 == 1:
            self <= html.DIV(Class="dot", style={"left": "40%", "top": "40%"})
        if n > 1:
            self <= html.DIV(Class="dot", style={"left": "0%", "top": "0%"})
            self <= html.DIV(Class="dot", style={"left": "80%", "top": "80%"})
        if n > 3:
            self <= html.DIV(Class="dot", style={"left": "80%", "top": "0%"})
            self <= html.DIV(Class="dot", style={"left": "0%", "top": "80%"})
        if n == 6:
            self <= html.DIV(Class="dot", style={"left": "0%", "top": "40%"})
            self <= html.DIV(Class="dot", style={"left": "80%", "top": "40%"})


class Domino(html.DIV):
    def __init__(self, n1, n2):
        html.DIV.__init__(
            self, "", style={"position": "absolute", "background-color": "black"}
        )
        self.values = (n1, n2)
        self.pos = None
        self.width = innersize + outersize
        self.height = innersize
        dots = Dotpattern(n1)
        dots.style = {"left": "5%", "top": "10%"}
        self <= dots
        dots = Dotpattern(n2)
        dots.style = {"left": "55%", "top": "10%"}
        self <= dots
        self.rotation = 0
        self.bind("mousedown", self.mousedown)
        self.bind("mouseup", self.mouseup)
        self.bind("touchstart", self.mousedown)
        self.bind("touchend", self.mouseup)

    def place(self, pos):
        if pos:
            self.pos = pos
            pos.domino = self
            self.style.transition = "all 0.5s"
            (self.left, self.top) = (
                game.board.left + self.pos.left + 2 * borderwidth,
                game.board.top + self.pos.top + 2 * borderwidth,
            )
            if pos.orientation == "V":
                if self.rotation in [0, 180]:
                    self.setrotation((self.rotation + 90) % 360)
            else:
                if self.rotation in [90, 270]:
                    self.setrotation((self.rotation - 90) % 360)
        else:
            self.pos = None
            self.style.transition = "all 1s"
            (self.left, self.top) = (self.originalleft, self.originaltop)
            self.setrotation(0)
        (self.startleft, self.starttop) = (self.left, self.top)
        self.style.backgroundColor = "black"

    def rotate(self):
        self.style.transition = "all 1s"
        self.setrotation((self.rotation + 180) % 360)
        if self.pos:
            (self.left, self.top) = (
                game.board.left + self.pos.left + 2 * borderwidth,
                game.board.top + self.pos.top + 2 * borderwidth,
            )
        else:
            (self.left, self.top) = (self.originalleft, self.originaltop)

    def setrotation(self, rotation):
        self.rotation = rotation
        if rotation in [90, 270]:
            self.transform = "translate(-{0}px,{0}px) rotate({1}deg)".format(
                outersize / 2, self.rotation
            )
        else:
            self.transform = "rotate({0}deg)".format(self.rotation)
        self.style.transform = self.transform
        self.style.webkitTransform = self.transform

    def mousedown(self, event):
        global touchevents
        if event.type == "touchstart":
            touchevents = True
        if touchevents and event.type == "mousedown":
            event.preventDefault()
            event.stopPropagation()
            return

        global drag, dragobject, Xdragstart, Ydragstart
        Xdragstart = (
            event.targetTouches[0].clientX
            if event.type == "touchstart"
            else event.clientX
        )
        Ydragstart = (
            event.targetTouches[0].clientY
            if event.type == "touchstart"
            else event.clientY
        )
        self.style.transition = ""
        document["game"] <= self
        drag = True
        dragobject = self
        event.preventDefault()
        event.stopPropagation()

    def mouseup(self, event):
        if touchevents and event.type == "mouseup":
            event.preventDefault()
            event.stopPropagation()
            return

        global drag, dragobject
        if drag:
            drag = False
            dragobject = None
            board = game.board
            currentX = (
                event.changedTouches[0].clientX
                if event.type == "touchend"
                else event.clientX
            )
            currentY = (
                event.changedTouches[0].clientY
                if event.type == "touchend"
                else event.clientY
            )
            dx = currentX - Xdragstart
            dy = currentY - Ydragstart
            if dx * dx + dy * dy < 25:
                self.rotate()
            else:
                if self.pos:
                    self.pos.domino = None
                if board.currentpos:
                    if board.currentpos.domino:
                        board.currentpos.domino.place(self.pos)
                    board.currentpos.style.backgroundColor = "inherit"
                    self.place(board.currentpos)
                else:
                    self.place(None)
            game.updatetotals()
        event.stopPropagation()


class Game(html.DIV):
    def __init__(self, level):
        html.DIV.__init__(
            self,
            "",
            id="game",
            style={
                "position": "relative",
                "display": "inline-block",
                "width": 12 * outersize,
                "height": "100%",
                "padding": 0,
            },
        )
        self.bind("mousemove", self.mousemove)
        self.bind("mouseup", self.mouseup)
        self.bind("touchmove", self.mousemove)
        self.level = 1
        # diffs = rowdiffs[level]
        pattern = patterns[choice(patternnumbers[level])]
        domcount = len(pattern)
        (boardwidth, boardheight) = (
            (4, 3) if domcount == 6 else (5, 4) if domcount == 10 else (6, 4)
        )

        self.board = Board(boardwidth, boardheight, pattern)
        self <= self.board

        dotcount = {(i, j): 0 for i in range(boardwidth) for j in range(boardheight)}

        extradoms = 1 if domcount == 6 else 2
        hi = True if randrange(2) else False
        (firstdom, lastdom) = mainrange[level]
        if hi:
            (firstdom, lastdom) = (28 - lastdom, 28 - firstdom)
        dots = sample(domdots[firstdom:lastdom], domcount - extradoms)
        (firstdom, lastdom) = extrarange[level]
        if hi:
            (firstdom, lastdom) = (28 - lastdom, 28 - firstdom)
        dots.extend(sample(domdots[firstdom:lastdom], extradoms))
        shuffle(dots)
        for i in range(domcount):
            j = randrange(2)
            dotcount[pattern[i][0]] = dots[i][j]
            dotcount[pattern[i][1]] = dots[i][1 - j]

        for rowno in range(boardheight):
            total = sum(dotcount[(i, rowno)] for i in range(boardwidth))
        for colno in range(boardwidth):
            total = sum(dotcount[(colno, j)] for j in range(boardheight))

        self.dominos = dominos = [Domino(*dotcounts) for dotcounts in dots]

        dominos.sort(key=lambda domino: domino.values)
        C = len(dominos) / 2
        for (i, d) in enumerate(dominos):
            L, T = divmod(i, C)
            d.originalleft = d.startleft = d.left = int(
                (2 * outersize + 5 * borderwidth) * L
            )
            d.originaltop = d.starttop = d.top = int((outersize + 2 * borderwidth) * T)
            d.index = i
            self <= d

    def clearboard(self):
        # tt = time()
        for p in self.board.poslist:
            if p.domino:
                p.domino.place(None)
                p.domino = None
        self.updatetotals()
        # print (time() - tt)

    def updatetotals(self):
        # This is called after each move. See what updates the server needs.
        pass

    def mousemove(self, event):
        if drag:
            currentX = (
                event.targetTouches[0].clientX
                if event.type == "touchmove"
                else event.clientX
            )
            currentY = (
                event.targetTouches[0].clientY
                if event.type == "touchmove"
                else event.clientY
            )
            dx = currentX - Xdragstart
            dy = currentY - Ydragstart
            dragobject.left = dragobject.startleft + dx
            dragobject.top = dragobject.starttop + dy
            board = self.board
            (i, j) = (
                (currentX - board.abs_left) // outersize,
                (currentY - board.abs_top) // outersize,
            )
            if board.currentpos and (i, j) != board.currentpos:
                board.currentpos.style.backgroundColor = "inherit"
                if board.currentpos.domino:
                    board.currentpos.domino.style.backgroundColor = "black"
            if (i, j) in board.squaredict:
                board.currentpos = board.squaredict[(i, j)]
                board.currentpos.style.backgroundColor = "white"
                if board.currentpos is not dragobject.pos and board.currentpos.domino:
                    board.currentpos.domino.style.transition = ""
                    board.currentpos.domino.style.backgroundColor = "white"
            else:
                board.currentpos = None
            event.preventDefault()
            event.stopPropagation()

    def mouseup(self, event):
        global drag, dragobject
        drag = False
        dragobject = None
        event.stopPropagation()


def setupgame(event):
    global game
    del document["game"]
    level = 1
    game = Game(level)
    document["drawarea"] <= game


def showwin():
    pass


def restart(event):
    game.clearboard()


touchevents = False
Xdragstart = 0
Ydragstart = 0
drag = False
dragobject = None

patterns = [
    [
        ((0, 0), (1, 0)),
        ((2, 0), (3, 0)),
        ((0, 1), (0, 2)),
        ((1, 1), (1, 2)),
        ((2, 1), (2, 2)),
        ((3, 1), (3, 2)),
    ],
    [
        ((0, 0), (1, 0)),
        ((2, 0), (3, 0)),
        ((0, 1), (0, 2)),
        ((1, 1), (2, 1)),
        ((1, 2), (2, 2)),
        ((3, 1), (3, 2)),
    ],
    [
        ((0, 0), (1, 0)),
        ((2, 2), (3, 2)),
        ((0, 1), (0, 2)),
        ((1, 1), (1, 2)),
        ((2, 0), (2, 1)),
        ((3, 0), (3, 1)),
    ],
    [
        ((0, 0), (1, 0)),
        ((3, 0), (4, 0)),
        ((0, 1), (1, 1)),
        ((3, 1), (4, 1)),
        ((0, 2), (1, 2)),
        ((3, 2), (4, 2)),
        ((0, 3), (1, 3)),
        ((3, 3), (4, 3)),
        ((2, 0), (2, 1)),
        ((2, 2), (2, 3)),
    ],
    [
        ((0, 0), (1, 0)),
        ((0, 1), (0, 2)),
        ((1, 1), (1, 2)),
        ((0, 3), (1, 3)),
        ((3, 0), (4, 0)),
        ((3, 1), (3, 2)),
        ((4, 1), (4, 2)),
        ((3, 3), (4, 3)),
        ((2, 0), (2, 1)),
        ((2, 2), (2, 3)),
    ],
    [
        ((0, 0), (1, 0)),
        ((0, 1), (1, 1)),
        ((0, 2), (0, 3)),
        ((1, 2), (1, 3)),
        ((3, 0), (3, 1)),
        ((4, 0), (4, 1)),
        ((3, 2), (4, 2)),
        ((3, 3), (4, 3)),
        ((2, 0), (2, 1)),
        ((2, 2), (2, 3)),
    ],
    [
        ((0, 0), (0, 1)),
        ((1, 0), (2, 0)),
        ((3, 0), (4, 0)),
        ((1, 1), (2, 1)),
        ((3, 1), (4, 1)),
        ((0, 2), (1, 2)),
        ((2, 2), (3, 2)),
        ((0, 3), (1, 3)),
        ((2, 3), (3, 3)),
        ((4, 2), (4, 3)),
    ],
    [
        ((0, 0), (1, 0)),
        ((0, 1), (1, 1)),
        ((0, 2), (0, 3)),
        ((1, 2), (1, 3)),
        ((2, 0), (2, 1)),
        ((3, 0), (3, 1)),
        ((2, 2), (3, 2)),
        ((2, 3), (3, 3)),
        ((4, 0), (5, 0)),
        ((4, 1), (5, 1)),
        ((4, 2), (4, 3)),
        ((5, 2), (5, 3)),
    ],
    [
        ((0, 0), (1, 0)),
        ((0, 1), (0, 2)),
        ((1, 1), (1, 2)),
        ((0, 3), (1, 3)),
        ((2, 0), (2, 1)),
        ((3, 0), (3, 1)),
        ((2, 2), (2, 3)),
        ((3, 2), (3, 3)),
        ((4, 0), (5, 0)),
        ((4, 1), (4, 2)),
        ((5, 1), (5, 2)),
        ((4, 3), (5, 3)),
    ],
    [
        ((0, 0), (0, 1)),
        ((0, 2), (0, 3)),
        ((1, 0), (2, 0)),
        ((3, 0), (4, 0)),
        ((1, 1), (1, 2)),
        ((2, 1), (3, 1)),
        ((2, 2), (3, 2)),
        ((4, 1), (4, 2)),
        ((1, 3), (2, 3)),
        ((3, 3), (4, 3)),
        ((5, 0), (5, 1)),
        ((5, 2), (5, 3)),
    ],
]

domdots = [
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 1),
    (0, 3),
    (1, 2),
    (0, 4),
    (1, 3),
    (2, 2),
    (0, 5),
    (1, 4),
    (2, 3),
    (0, 6),
    (1, 5),
    (2, 4),
    (3, 3),
    (1, 6),
    (2, 5),
    (3, 4),
    (4, 4),
    (3, 5),
    (2, 6),
    (4, 5),
    (3, 6),
    (5, 5),
    (4, 6),
    (5, 6),
    (6, 6),
]

mainrange = {
    1: (0, 9),
    2: (0, 19),
    3: (3, 25),
    4: (0, 19),
    5: (0, 19),
    6: (3, 25),
    7: (0, 28),
    8: (3, 25),
}
extrarange = {
    1: (0, 9),
    2: (0, 19),
    3: (3, 25),
    4: (0, 19),
    5: (20, 28),
    6: (0, 28),
    7: (0, 28),
    8: (0, 28),
}

rowdiffs = {1: "EEM", 2: "EMM", 3: "MMH", 4: "EMMM", 5: "MMMH", 6: "HHHH"}

patternnumbers = {
    1: [0],
    2: [1],
    3: [2],
    4: [3, 4],
    5: [4, 5],
    6: [5, 6],
    7: [7, 8],
    8: [8, 9],
}

document["startgame"].bind("click", setupgame)
document["restart"].bind("click", restart)

(boxwidth, boxheight) = (
    document["drawarea"].clientWidth,
    document["drawarea"].clientHeight,
)
headerheight = document["header"].clientHeight
controlsheight = document["controls"].clientHeight
innersize = int(min(boxwidth / 14, (boxheight - headerheight - controlsheight) / 7))
borderwidth = int(innersize / 20)
outersize = innersize + 2 * borderwidth

setupgame(None)
