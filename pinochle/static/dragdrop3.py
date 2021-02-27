from browser import document, alert, svg
from browser.timer import set_timeout
import browser.html as html
from random import randrange, choice, shuffle, sample


class Board(html.DIV):
    def __init__(self, boardwidth, boardheight, pattern):
        html.DIV.__init__(
            self,
            "",
            style={
                "position": "absolute",
                "background-color": "grey",
                "border": "{0}px solid black".format(borderwidth),
            },
        )
        self.boardwidth = boardwidth
        self.boardheight = int(innersize / 0.69) * boardheight
        self.left = innersize * 5
        self.top = 0
        self.width = outersize * boardwidth
        self.height = self.boardheight + int(outersize / 2) # outersize * boardheight
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
                "border": "{0}px solid green".format(borderwidth),
                "background-color": "inherit",
            },
        )
        self.orientation = "V"
        self.width = innersize
        self.height = int(innersize / 0.69)
        self.left = outersize * pos[0][0]
        self.top = outersize * pos[0][1]
        self.squares = pos
        self.domino = None


class Domino(html.DIV):
    def __init__(self, n1, n2):
        html.DIV.__init__(
            self, "", style={"position": "absolute", "background-color": "gray"}
        )
        self.values = (n1, n2)
        self.pos = None
        self.width = innersize
        self.height = int(innersize / 0.69)
        card = html.SVG(style={"width": self.width, "height": self.height})
        card <= svg.use(
            href=f"/static/svg-cards.svg#heart_{n2}",
            transform=f"scale({self.width / 170})",
        )
        self <= card

        self.rotation = 0
        self.bind("mousedown", self.mousedown)
        self.bind("mouseup", self.mouseup)
        self.bind("touchstart", self.mousedown)
        self.bind("touchend", self.mouseup)

    def place(self, pos):
        if pos:
            # Place the card in the appropriate slot on the board.
            self.pos = pos
            pos.domino = self
            self.style.transition = "all 0.5s"
            (self.left, self.top) = (
                game.board.left + self.pos.left + 2 * borderwidth,
                game.board.top + self.pos.top + 2 * borderwidth,
            )
        else:
            # Put the card back where it came from.
            self.pos = None
            self.style.transition = "all 0.5s"
            (self.left, self.top) = (self.originalleft, self.originaltop)
            self.setrotation(0)
        (self.startleft, self.starttop) = (self.left, self.top)
        self.style.backgroundColor = "gray"

    def rotate(self):
        self.style.transition = "all 0.5s"
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
            currentX = event.changedTouches[0].clientX if event.type == "touchend" else event.clientX
            currentY = event.changedTouches[0].clientY if event.type == "touchend" else event.clientY
            dx = currentX - Xdragstart
            dy = currentY - Ydragstart

            # This is what rotates the card on touch. Don't need it.
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
            # game.updatetotals()
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
                "width": "100%",
                "height": "100%",
                "padding": 0,
            },
        )
        self.bind("mousemove", self.mousemove)
        self.bind("mouseup", self.mouseup)
        self.bind("touchmove", self.mousemove)
        self.level = level

        pattern = [
            ((0, 0), (1, 0)),
            ((2, 0), (3, 0)),
            ((4, 0), (5, 0)),
            ((6, 0), (7, 0)),
            ((8, 0), (9, 0)),
            ((10, 0), (11, 0)),
        ]

        domcount = len(pattern)
        (boardwidth, boardheight) = (13, 2)

        self.board = Board(boardwidth, boardheight, pattern)
        self <= self.board

        dotcount = {(i, j): 0 for i in range(boardwidth) for j in range(boardheight)}

        extradoms = 1 if domcount == 6 else 2
        hi = True if randrange(2) else False
        (firstdom, lastdom) = (0, 9)
        if hi:
            (firstdom, lastdom) = (28 - lastdom, 28 - firstdom)
        dots = sample(domdots[firstdom:lastdom], domcount - extradoms)
        (firstdom, lastdom) = (0, 9)
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
            d.originaltop = d.starttop = d.top = (outersize + 2 * borderwidth) * T
            d.index = i
            self <= d

    def clearboard(self):
        for p in self.board.poslist:
            if p.domino:
                p.domino.place(None)
                p.domino = None
        # self.updatetotals()

    def updatetotals(self):
        # Called every time a card is moved. Send information back to the server if 
        # something important happened.

        if winner:
            set_timeout(showwin, 1500)

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
    document["rank"].text = "You win!"


def restart(event):
    game.clearboard()


touchevents = False
Xdragstart = 0
Ydragstart = 0
drag = False
dragobject = None

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

document["startgame"].bind("click", setupgame)
document["restart"].bind("click", restart)

(boxwidth, boxheight) = (
    document["drawarea"].clientWidth,
    document["drawarea"].clientHeight,
)
headerheight = document["header"].clientHeight
controlsheight = document["controls"].clientHeight
innersize = int(min(boxwidth / 4, (boxheight - headerheight - controlsheight) / 4))
borderwidth = int(innersize / 20)
outersize = int(innersize * 0.69)  # + 2 * borderwidth

setupgame(None)
