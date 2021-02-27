from browser import document, alert
from browser.timer import set_timeout
import browser.html as html
from random import randrange, choice, shuffle, sample
#from time import time

class Board(html.DIV):
    def __init__(self, boardwidth, boardheight, pattern):
        html.DIV.__init__(self, "", style={"position":"absolute", "background-color":"#dc8264", "border":"{0}px solid #820a0a".format(borderwidth)})
        self.boardwidth = boardwidth
        self.boardheight = boardheight
        self.left = innersize*5
        self.top = 0
        self.width = outersize*boardwidth
        self.height = outersize*boardheight
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
        html.DIV.__init__(self, "", style={"position":"absolute", "border":"{0}px solid #820a0a".format(borderwidth), "background-color":"inherit"})
        self.orientation = "V" if pos[0][0] == pos[1][0] else "H"
        self.width = innersize if self.orientation == "V" else innersize+outersize
        self.height = innersize+outersize if self.orientation == "V" else innersize
        self.left = outersize*pos[0][0]
        self.top = outersize*pos[0][1]
        self.squares = pos
        self.domino = None

class RowTotals(html.DIV):
    def __init__(self, board):
        html.DIV.__init__(self, "", style={"position":"absolute", "border":"{0}px solid #820a0a".format(borderwidth), "font-size":"{0}px".format(innersize*0.7), "text-align":"center", "line-height":"{0}px".format(innersize)})
        self.left = board.left+board.width+int(innersize/2)
        self.top = board.top
        self.width = outersize*2
        self.height = outersize*board.boardheight
        self.requiredtotals = []
        self.currenttotals = []
        for rowindex in range(board.boardheight):
            t = RequiredTotal("R", rowindex, 17)
            self.requiredtotals.append(t)
            self <= t
            t = CurrentTotal("R", rowindex, 0)
            self.currenttotals.append(t)
            self <= t

class ColumnTotals(html.DIV):
    def __init__(self, board):
        html.DIV.__init__(self, "", style={"position":"absolute", "border":"{0}px solid #820a0a".format(borderwidth), "font-size":"{0}px".format(innersize*0.7), "text-align":"center", "line-height":"{0}px".format(innersize)})
        self.left = board.left
        self.top = board.top + board.height + int(innersize/2)
        self.width = outersize*board.boardwidth
        self.height = outersize*2
        self.requiredtotals = []
        self.currenttotals = []
        for colindex in range(board.boardwidth):
            t = RequiredTotal("C", colindex, 17)
            self.requiredtotals.append(t)
            self <= t
            t = CurrentTotal("C", colindex, 0)
            self.currenttotals.append(t)
            self <= t

class RequiredTotal(html.DIV):
    def __init__(self, line, index, total):
        html.DIV.__init__(self, "", style={"position":"absolute", "border":"{0}px solid #820a0a".format(borderwidth), "background-color":"limegreen"})
        self.left = outersize*index if line == "C" else outersize
        self.top = outersize*index if line == "R" else outersize
        self.width = self.height = innersize
        self.total = total
        self.text = total

class CurrentTotal(html.DIV):
    def __init__(self, line, index, total):
        html.DIV.__init__(self, "", style={"position":"absolute", "border":"{0}px solid #820a0a".format(borderwidth), "background-color":"inherit"})
        self.left = outersize*index if line == "C" else 0
        self.top = outersize*index if line == "R" else 0
        self.width = self.height = innersize
        self.text = total

class Dotpattern(html.DIV):
    def __init__(self, n):
        html.DIV.__init__(self, "", style={"position":"absolute", 'height':"80%", 'width':"40%", "background-color":"#1F1F1F"})
        if n%2 == 1:
            self <= html.DIV(Class="dot", style={'left':"40%", 'top':"40%"})
        if n > 1:
            self <= html.DIV(Class="dot", style={'left':"0%", 'top':"0%"})
            self <= html.DIV(Class="dot", style={'left':"80%", 'top':"80%"})
        if n > 3:
            self <= html.DIV(Class="dot", style={'left':"80%", 'top':"0%"})
            self <= html.DIV(Class="dot", style={'left':"0%", 'top':"80%"})
        if n == 6:
            self <= html.DIV(Class="dot", style={'left':"0%", 'top':"40%"})
            self <= html.DIV(Class="dot", style={'left':"80%", 'top':"40%"})


class Domino(html.DIV):
    def __init__(self, n1, n2):
        html.DIV.__init__(self, "", style={"position":"absolute", "background-color":"black"})
        self.values = (n1, n2)
        self.pos = None
        self.width = innersize+outersize
        self.height = innersize
        dots = Dotpattern(n1)
        dots.style={'left':"5%", 'top':"10%"}
        self <= dots
        dots = Dotpattern(n2)
        dots.style={'left':"55%", 'top':"10%"}
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
            (self.left, self.top) = (game.board.left + self.pos.left + 2*borderwidth, game.board.top + self.pos.top + 2*borderwidth)
            if pos.orientation == "V":
                if self.rotation in [0, 180]: self.setrotation((self.rotation + 90) % 360)
            else:
                if self.rotation in [90, 270]: self.setrotation((self.rotation - 90) % 360)
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
            (self.left, self.top) = (game.board.left+self.pos.left + 2*borderwidth, game.board.top+self.pos.top + 2*borderwidth)
        else:
            (self.left, self.top) = (self.originalleft, self.originaltop)

    def setrotation(self, rotation):
        self.rotation = rotation
        if rotation in [90, 270]:
            self.transform = "translate(-{0}px,{0}px) rotate({1}deg)".format(outersize/2, self.rotation)
        else:
            self.transform = "rotate({0}deg)".format(self.rotation)
        self.style.transform = self.transform
        self.style.webkitTransform = self.transform

    def mousedown(self, event):
        global touchevents
        if event.type == "touchstart": touchevents = True
        if touchevents and event.type == "mousedown":
            event.preventDefault()
            event.stopPropagation()
            return

        global drag, dragobject, Xdragstart, Ydragstart
        Xdragstart = event.targetTouches[0].clientX if event.type == "touchstart" else event.clientX
        Ydragstart = event.targetTouches[0].clientY if event.type == "touchstart" else event.clientY
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
            dx = currentX-Xdragstart
            dy = currentY-Ydragstart
            if dx*dx+dy*dy < 25:
                self.rotate()
            else:
                if self.pos: self.pos.domino = None
                if board.currentpos:
                    if board.currentpos.domino: board.currentpos.domino.place(self.pos)
                    board.currentpos.style.backgroundColor = "inherit"
                    self.place(board.currentpos)
                else:
                    self.place(None)
            game.updatetotals()
        event.stopPropagation()

class Game(html.DIV):
    def __init__(self, level):
        html.DIV.__init__(self, "", id="game", style={"position":"relative", "display":"inline-block", "width":12*outersize, "height":"100%", "padding":0})
        self.bind("mousemove",self.mousemove)
        self.bind("mouseup",self.mouseup)
        self.bind("touchmove",self.mousemove)
        self.level = level
        #diffs = rowdiffs[level]
        pattern = patterns[choice(patternnumbers[level])]
        domcount = len(pattern)
        (boardwidth, boardheight) = (4, 3) if domcount == 6 else (5, 4) if domcount == 10 else (6, 4)

        self.board = Board(boardwidth, boardheight, pattern)
        self <= self.board
        self.rowtotals = RowTotals(self.board)
        self <= self.rowtotals
        self.coltotals = ColumnTotals(self.board)
        self <= self.coltotals

        dotcount = {(i,j):0 for i in range(boardwidth) for j in range(boardheight)}
        """
        direction = "H" if randrange(2) else "V"
        if direction == "H":
            shuffle(list(diffs))
            for rowno, diff in enumerate(diffs):
                for i, spots in enumerate(randomline(boardwidth, diff)):
                    dotcount[(i, rowno)] = spots
        else:
            diffs += "H" if level == 6 else "M"
            shuffle(list(diffs))
            for colno, diff in enumerate(diffs):
                for j, spots in enumerate(randomline(boardheight, diff)):
                    dotcount[(colno, j)] = spots
        """
        extradoms = 1 if domcount == 6 else 2
        hi = True if randrange(2) else False
        (firstdom, lastdom) = mainrange[level]
        if hi: (firstdom, lastdom) = (28-lastdom, 28-firstdom)
        dots = sample(domdots[firstdom:lastdom], domcount-extradoms)
        (firstdom, lastdom) = extrarange[level]
        if hi: (firstdom, lastdom) = (28-lastdom, 28-firstdom)
        dots.extend(sample(domdots[firstdom:lastdom], extradoms))
        shuffle(dots)
        for i in range(domcount):
            j = randrange(2)
            dotcount[pattern[i][0]] = dots[i][j]
            dotcount[pattern[i][1]] = dots[i][1-j]

        for rowno in range(boardheight):
            total = sum(dotcount[(i, rowno)] for i in range(boardwidth))
            self.rowtotals.requiredtotals[rowno].total = total
            self.rowtotals.requiredtotals[rowno].text = total
        for colno in range(boardwidth):
            total = sum(dotcount[(colno, j)] for j in range(boardheight))
            self.coltotals.requiredtotals[colno].total = total
            self.coltotals.requiredtotals[colno].text = total

        self.dominos = dominos = [Domino(*dotcounts) for dotcounts in dots]
        """
        dominos = []
        for pos in pattern:
            (n1, n2) = (dotcount[pos[0]], dotcount[pos[1]])
            if n1>n2: (n1, n2) = (n2, n1)
            dominos.append(Domino(n1, n2))
        """
        dominos.sort(key = lambda domino: domino.values)
        C = len(dominos)/2
        for (i, d) in enumerate(dominos):
            L, T = divmod(i, C)
            d.originalleft = d.startleft = d.left = int((2*outersize+5*borderwidth)*L)
            d.originaltop = d.starttop = d.top = int((outersize+2*borderwidth)*T)
            d.index = i
            self <= d

    def clearboard(self):
        #tt = time()
        for p in self.board.poslist:
            if p.domino:
                p.domino.place(None)
                p.domino = None
        self.updatetotals()
        #print (time() - tt)

    def updatetotals(self):
        (boardwidth, boardheight) = (self.board.boardwidth, self.board.boardheight)
        dotcount = {(i,j):0 for i in range(boardwidth) for j in range(boardheight)}
        winner = True
        for pos in self.board.poslist:
            domino = pos.domino
            if domino:
                for (i, square) in enumerate(pos.squares):
                    dotcount[square] = domino.values[i] if domino.rotation in [0,90] else domino.values[1-i]
            else:
                winner = False

        for rowno in range(boardheight):
            total = sum(dotcount[(i, rowno)] for i in range(boardwidth))
            self.rowtotals.currenttotals[rowno].text = total
            if total == self.rowtotals.requiredtotals[rowno].total:
                self.rowtotals.currenttotals[rowno].style.backgroundColor = "limegreen"
            elif total > self.rowtotals.requiredtotals[rowno].total:
                self.rowtotals.currenttotals[rowno].style.backgroundColor = "red"
                winner = False
            else:
                self.rowtotals.currenttotals[rowno].style.backgroundColor = "inherit"
                winner = False

        for colno in range(boardwidth):
            total = sum(dotcount[(colno, j)] for j in range(boardheight))
            self.coltotals.currenttotals[colno].text = total
            if total == self.coltotals.requiredtotals[colno].total:
                self.coltotals.currenttotals[colno].style.backgroundColor = "limegreen"
            elif total > self.coltotals.requiredtotals[colno].total:
                self.coltotals.currenttotals[colno].style.backgroundColor = "red"
                winner = False
            else:
                self.coltotals.currenttotals[colno].style.backgroundColor = "inherit"
                winner = False

        if winner:
            set_timeout(showwin, 1500)

    def mousemove(self, event):
        if drag:
            currentX = event.targetTouches[0].clientX if event.type == "touchmove" else event.clientX
            currentY = event.targetTouches[0].clientY if event.type == "touchmove" else event.clientY
            dx = currentX-Xdragstart
            dy = currentY-Ydragstart
            dragobject.left = dragobject.startleft+dx
            dragobject.top = dragobject.starttop+dy
            board = self.board
            (i, j) = ((currentX - board.abs_left)//outersize, (currentY - board.abs_top)//outersize)
            if board.currentpos and (i, j) != board.currentpos:
                board.currentpos.style.backgroundColor = "inherit"
                if board.currentpos.domino: board.currentpos.domino.style.backgroundColor = "black"
            if (i, j) in board.squaredict:
                board.currentpos = board.squaredict[(i,j)]
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
    document["winner"].style.display = "none"
    del document["game"]
    level = int(document["level"].value)
    game = Game(level)
    document["drawarea"] <= game

def randomline(count, difficulty):
    difficulty += "H" if randrange(2) else "L"
    rlist = choice(alllists[difficulty])
    while len(rlist) < count:
        rlist.append(choice(extralists[difficulty]))
    shuffle(rlist)
    return rlist

def showwin():
    document["rank"].text = levels[game.level]+" Dominator"
    document["winner"].style.display = "block"

def restart(event):
    game.clearboard()

def showrules(event):
    alert(rules)

rules = """How to play:
Drag the dominos onto the board, arranging them so that the total number of spots in each row and column is equal to the number in the green box.

To rotate a domino, click or tap on it.

To replace a domino, drag another one on top of it.  The dominos will swap places.

To start a new game, choose a different level, or click "New game".

To remove a domino from the board, just drag it anywhere off the board.
To remove all dominos from the board, click "Restart".
"""

touchevents = False
Xdragstart = 0
Ydragstart = 0
drag = False
dragobject = None

patterns = [
[((0,0), (1,0)), ((2,0), (3,0)), ((0,1), (0,2)), ((1,1), (1,2)), ((2,1), (2,2)), ((3,1), (3,2))],
[((0,0), (1,0)), ((2,0), (3,0)), ((0,1), (0,2)), ((1,1), (2,1)), ((1,2), (2,2)), ((3,1), (3,2))],
[((0,0), (1,0)), ((2,2), (3,2)), ((0,1), (0,2)), ((1,1), (1,2)), ((2,0), (2,1)), ((3,0), (3,1))],
[((0,0), (1,0)), ((3,0), (4,0)), ((0,1), (1,1)), ((3,1), (4,1)), ((0,2), (1,2)), ((3,2), (4,2)), ((0,3), (1,3)), ((3,3), (4,3)), ((2,0), (2,1)), ((2,2), (2,3))],
[((0,0), (1,0)), ((0,1), (0,2)), ((1,1), (1,2)), ((0,3), (1,3)), ((3,0), (4,0)), ((3,1), (3,2)), ((4,1), (4,2)), ((3,3), (4,3)), ((2,0), (2,1)), ((2,2), (2,3))],
[((0,0), (1,0)), ((0,1), (1,1)), ((0,2), (0,3)), ((1,2), (1,3)), ((3,0), (3,1)), ((4,0), (4,1)), ((3,2), (4,2)), ((3,3), (4,3)), ((2,0), (2,1)), ((2,2), (2,3))],
[((0,0), (0,1)), ((1,0), (2,0)), ((3,0), (4,0)), ((1,1), (2,1)), ((3,1), (4,1)), ((0,2), (1,2)), ((2,2), (3,2)), ((0,3), (1,3)), ((2,3), (3,3)), ((4,2), (4,3))],
[((0,0), (1,0)), ((0,1), (1,1)), ((0,2), (0,3)), ((1,2), (1,3)), ((2,0), (2,1)), ((3,0), (3,1)), ((2,2), (3,2)), ((2,3), (3,3)), ((4,0), (5,0)), ((4,1), (5,1)), ((4,2), (4,3)), ((5,2), (5,3))],
[((0,0), (1,0)), ((0,1), (0,2)), ((1,1), (1,2)), ((0,3), (1,3)), ((2,0), (2,1)), ((3,0), (3,1)), ((2,2), (2,3)), ((3,2), (3,3)), ((4,0), (5,0)), ((4,1), (4,2)), ((5,1), (5,2)), ((4,3), (5,3))],
[((0,0), (0,1)), ((0,2), (0,3)), ((1,0), (2,0)), ((3,0), (4,0)), ((1,1), (1,2)), ((2,1), (3,1)), ((2,2), (3,2)), ((4,1), (4,2)), ((1,3), (2,3)), ((3,3), (4,3)), ((5,0), (5,1)), ((5,2), (5,3))]
]

domdots = [(0,0),(0,1),(0,2),(1,1),(0,3),(1,2),(0,4),(1,3),(2,2),(0,5),(1,4),(2,3),(0,6),(1,5),(2,4),(3,3),(1,6),(2,5),(3,4),(4,4),(3,5),(2,6),(4,5),(3,6),(5,5),(4,6),(5,6),(6,6)]

mainrange = {1:(0,9), 2:(0,19), 3:(3,25), 4:(0,19), 5:(0,19), 6:(3,25), 7:(0,28), 8:(3,25)}
extrarange = {1:(0,9), 2:(0,19), 3:(3,25), 4:(0,19), 5:(20,28), 6:(0,28), 7:(0,28), 8:(0,28)}


alllists = {
"EL": [ [0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 1, 1] ],
"ML": [ [1, 1, 1], [1, 1, 2], [1, 1, 3], [1, 2, 2] ],
"HL": [ [2, 2, 2], [2, 2, 3], [2, 2, 4], [2, 3, 3], [2, 3, 4] ],
"HH": [ [3, 3, 3], [2, 4, 4], [3, 3, 4], [3, 4, 4], [4, 4, 4] ],
"MH": [ [3, 5, 5], [4, 4, 5], [4, 5, 5], [5, 5, 5] ],
"EH": [ [4, 6, 6], [5, 5, 6], [5, 6, 6], [6, 6, 6] ] }

extralists = {
"EL": [0, 1],
"ML": [0, 1, 2, 3],
"HL": [1, 2, 3, 4, 5, 6],
"HH": [0, 1, 2, 3, 4, 5],
"MH": [3, 4, 5, 6],
"EH": [5, 6] }

rowdiffs = {1:"EEM", 2:"EMM", 3:"MMH", 4:"EMMM", 5:"MMMH", 6:"HHHH"}
levels = {1:"Novice", 2:"Apprentice", 3:"Qualified", 4:"Senior", 5:"Expert", 6:"Master", 7:"Grand Master", 8:"Supreme Master"}
patternnumbers = {1:[0], 2:[1], 3:[2], 4:[3,4], 5:[4,5], 6:[5,6], 7:[7,8], 8:[8,9]}

document['level'] <= (html.OPTION(str(i)+" - "+levels[i], value=i) for i in range(1,9))
document["level"].bind("change",setupgame)
document["startgame"].bind("click",setupgame)
document["restart"].bind("click",restart)
document["showrules"].bind("click",showrules)

(boxwidth, boxheight) = (document["drawarea"].clientWidth, document["drawarea"].clientHeight)
headerheight = document["header"].clientHeight
controlsheight = document["controls"].clientHeight
innersize = int(min(boxwidth/14, (boxheight-headerheight-controlsheight)/7))
borderwidth = int(innersize/20)
outersize = innersize+2*borderwidth

setupgame(None)
