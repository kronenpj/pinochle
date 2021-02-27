# import math
from sys import stderr

from browser import document, svg
import brySVG.polygoncanvas as SVG

def checkposition(event):
    # event.preventDefault()
    pass

def clearintersections(event):
    # event.allowDefault()
    pass

# SVGRoot = document["svg_root"]
SVGRoot = document["card_table"]

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", "cyan", objid="canvas")
SVGRoot <= canvas

canvas.mouseMode = SVG.MouseMode.DRAG

# this will serve as the canvas over which items are dragged.
# having the drag events occur on the mousemove over a backdrop
# (instead of the dragged element) prevents the dragged element
# from being inadvertantly dropped when the mouse is moved rapidly
# outline = SVG.PolygonObject([(180, 100), (280,100), (280,200), (180,200)], fillcolour="none")
# canvas.addObject(outline, fixed=True)


xincr = 60
yincr = 80
xpos = 0
ypos = 0

for card in ["ace", "king", "queen", "jack"]:
    for suit in ["heart", "diamond", "spade", "club"]:
        piece = svg.use(
            href="/static/svg-cards.svg#" + f"{suit}_{card}"
            # , x=xpos, y=ypos
            #, transform="scale(0.5)"
        )
        canvas.addObject(piece)
        # canvas.translateObject(piece, (xpos, ypos))
        canvas.translateElement(piece, (xpos, ypos))
        xpos += xincr
    # xpos = 0
    # ypos += yincr

# canvas.fitContents()
