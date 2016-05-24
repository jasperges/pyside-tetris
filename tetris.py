#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZetCode PySide tutorial

This is a simple Tetris clone
in PySide.

author: Jan Bodnar
modifications: Jasper van Nieuwenhuizen
website: zetcode.com
last edited: May 2015
"""

import sys
import random
from collections import namedtuple
from PySide import QtCore
from PySide import QtGui


field_names = [
    'no_shape',
    'z_shape',
    's_shape',
    'line_shape',
    't_shape',
    'square_shape',
    'l_shape',
    'mirrored_l_shape',
    ]
Tetrominoes = namedtuple('Tetronimoes', field_names)
TETROMINOES = Tetrominoes(0, 1, 2, 3, 4, 5, 6, 7)


class Communicate(QtCore.QObject):

    msgToSB = QtCore.Signal(str)


class Tetris(QtGui.QMainWindow):

    def __init__(self):
        super(Tetris, self).__init__()

        self.setGeometry(300, 300, 180, 380)
        self.setWindowTitle('Tetris')
        self.Tetrisboard = Board(self)

        self.setCentralWidget(self.Tetrisboard)

        self.statusbar = self.statusBar()
        self.Tetrisboard.c.msgToSB[str].connect(self.statusbar.showMessage)

        self.Tetrisboard.start()
        self.center()

    def center(self):

        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)


class Board(QtGui.QFrame):

    board_width = 10
    board_height = 22
    speed = 300

    def __init__(self, parent):
        super(Board, self).__init__()

        self.timer = QtCore.QBasicTimer()
        self.isWaitingAfterLine = False
        self.curPiece = Shape()
        self.nextPiece = Shape()
        self.curX = 0
        self.curY = 0
        self.numLinesRemoved = 0
        self.board = []

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.isStarted = False
        self.isPaused = False
        self.clearBoard()

        self.c = Communicate()

        self.nextPiece.setRandomShape()

    def shapeAt(self, x, y):
        x = int(x)
        y = int(y)
        return self.board[(y * Board.board_width) + x]

    def setShapeAt(self, x, y, shape):
        x = int(x)
        y = int(y)
        self.board[(y * Board.board_width) + x] = shape

    def squareWidth(self):
        return self.contentsRect().width() / Board.board_width

    def squareHeight(self):
        return self.contentsRect().height() / Board.board_height

    def start(self):
        if self.isPaused:
            return

        self.isStarted = True
        self.isWaitingAfterLine = False
        self.numLinesRemoved = 0
        self.clearBoard()

        self.c.msgToSB.emit(str(self.numLinesRemoved))

        self.newPiece()
        self.timer.start(Board.speed, self)

    def pause(self):

        if not self.isStarted:
            return

        self.isPaused = not self.isPaused

        if self.isPaused:
            self.timer.stop()
            self.c.msgToSB.emit("paused")
        else:
            self.timer.start(Board.speed, self)
            self.c.msgToSB.emit(str(self.numLinesRemoved))

        self.update()

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        rect = self.contentsRect()

        boardTop = rect.bottom() - Board.board_height * self.squareHeight()

        for i in range(Board.board_height):
            for j in range(Board.board_width):
                shape = self.shapeAt(j, Board.board_height - i - 1)
                if shape != TETROMINOES.no_shape:
                    self.drawSquare(painter,
                        rect.left() + j * self.squareWidth(),
                        boardTop + i * self.squareHeight(), shape)

        if self.curPiece.shape() != TETROMINOES.no_shape:
            for i in range(4):
                x = self.curX + self.curPiece.x(i)
                y = self.curY - self.curPiece.y(i)
                self.drawSquare(painter, rect.left() + x * self.squareWidth(),
                    boardTop + (Board.board_height - y - 1) * self.squareHeight(),
                    self.curPiece.shape())

    def keyPressEvent(self, event):

        if not self.isStarted or self.curPiece.shape() == TETROMINOES.no_shape:
            QtGui.QWidget.keyPressEvent(self, event)
            return

        key = event.key()

        if key == QtCore.Qt.Key_P:
            self.pause()
            return
        if self.isPaused:
            return
        elif key == QtCore.Qt.Key_Left:
            self.tryMove(self.curPiece, self.curX - 1, self.curY)
        elif key == QtCore.Qt.Key_Right:
            self.tryMove(self.curPiece, self.curX + 1, self.curY)
        elif key == QtCore.Qt.Key_Down:
            self.tryMove(self.curPiece.rotatedRight(), self.curX, self.curY)
        elif key == QtCore.Qt.Key_Up:
            self.tryMove(self.curPiece.rotatedLeft(), self.curX, self.curY)
        elif key == QtCore.Qt.Key_Space:
            self.dropDown()
        elif key == QtCore.Qt.Key_D:
            self.oneLineDown()
        else:
            QtGui.QWidget.keyPressEvent(self, event)

    def timerEvent(self, event):

        if event.timerId() == self.timer.timerId():
            if self.isWaitingAfterLine:
                self.isWaitingAfterLine = False
                self.newPiece()
            else:
                self.oneLineDown()
        else:
            QtGui.QFrame.timerEvent(self, event)

    def clearBoard(self):

        for i in range(Board.board_height * Board.board_width):
            self.board.append(TETROMINOES.no_shape)

    def dropDown(self):

        newY = self.curY
        while newY > 0:
            if not self.tryMove(self.curPiece, self.curX, newY - 1):
                break
            newY -= 1

        self.pieceDropped()

    def oneLineDown(self):

        if not self.tryMove(self.curPiece, self.curX, self.curY - 1):
            self.pieceDropped()

    def pieceDropped(self):

        for i in range(4):
            x = self.curX + self.curPiece.x(i)
            y = self.curY - self.curPiece.y(i)
            self.setShapeAt(x, y, self.curPiece.shape())

        self.removeFullLines()

        if not self.isWaitingAfterLine:
            self.newPiece()

    def removeFullLines(self):
        numFullLines = 0

        rowsToRemove = []

        for i in range(Board.board_height):
            n = 0
            for j in range(Board.board_width):
                if not self.shapeAt(j, i) == TETROMINOES.no_shape:
                    n = n + 1

            if n == 10:
                rowsToRemove.append(i)

        rowsToRemove.reverse()

        for m in rowsToRemove:
            for k in range(m, Board.board_height):
                for l in range(Board.board_width):
                        self.setShapeAt(l, k, self.shapeAt(l, k + 1))

        numFullLines = numFullLines + len(rowsToRemove)

        if numFullLines > 0:
            self.numLinesRemoved = self.numLinesRemoved + numFullLines
            print(self.numLinesRemoved)
            self.c.msgToSB.emit(str(self.numLinesRemoved))
            self.isWaitingAfterLine = True
            self.curPiece.setShape(TETROMINOES.no_shape)
            self.update()

    def newPiece(self):

        self.curPiece = self.nextPiece
        self.nextPiece.setRandomShape()
        self.curX = Board.board_width / 2 + 1
        self.curY = Board.board_height - 1 + self.curPiece.minY()

        if not self.tryMove(self.curPiece, self.curX, self.curY):
            self.curPiece.setShape(TETROMINOES.no_shape)
            self.timer.stop()
            self.isStarted = False
            self.c.msgToSB.emit("Game over")

    def tryMove(self, newPiece, newX, newY):

        for i in range(4):
            x = newX + newPiece.x(i)
            y = newY - newPiece.y(i)
            if x < 0 or x >= Board.board_width or y < 0 or y >= Board.board_height:
                return False
            if self.shapeAt(x, y) != TETROMINOES.no_shape:
                return False

        self.curPiece = newPiece
        self.curX = newX
        self.curY = newY
        self.update()
        return True

    def drawSquare(self, painter, x, y, shape):

        colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]

        color = QtGui.QColor(colorTable[shape])
        painter.fillRect(x + 1, y + 1, self.squareWidth() - 2,
            self.squareHeight() - 2, color)

        painter.setPen(color.lighter())
        painter.drawLine(x, y + self.squareHeight() - 1, x, y)
        painter.drawLine(x, y, x + self.squareWidth() - 1, y)

        painter.setPen(color.darker())
        painter.drawLine(x + 1, y + self.squareHeight() - 1,
            x + self.squareWidth() - 1, y + self.squareHeight() - 1)
        painter.drawLine(x + self.squareWidth() - 1,
            y + self.squareHeight() - 1, x + self.squareWidth() - 1, y + 1)



class Shape(object):

    coordsTable = (
        ((0, 0), (0, 0), (0, 0), (0, 0)),
        ((0, -1), (0, 0), (-1, 0), (-1, 1)),
        ((0, -1), (0, 0), (1, 0), (1, 1)),
        ((0, -1), (0, 0), (0, 1), (0, 2)),
        ((-1, 0), (0, 0), (1, 0), (0, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((-1, -1), (0, -1), (0, 0), (0, 1)),
        ((1, -1), (0, -1), (0, 0), (0, 1))
    )

    def __init__(self):

        self.coords = [[0,0] for i in range(4)]
        self.pieceShape = TETROMINOES.no_shape

        self.setShape(TETROMINOES.no_shape)

    def shape(self):
        return self.pieceShape

    def setShape(self, shape):

        table = Shape.coordsTable[shape]
        for i in range(4):
            for j in range(2):
                self.coords[i][j] = table[i][j]

        self.pieceShape = shape

    def setRandomShape(self):
        self.setShape(random.randint(1, 7))

    def x(self, index):
        return self.coords[index][0]

    def y(self, index):
        return self.coords[index][1]

    def setX(self, index, x):
        self.coords[index][0] = x

    def setY(self, index, y):
        self.coords[index][1] = y

    def minX(self):

        m = self.coords[0][0]
        for i in range(4):
            m = min(m, self.coords[i][0])

        return m

    def maxX(self):

        m = self.coords[0][0]
        for i in range(4):
            m = max(m, self.coords[i][0])

        return m

    def minY(self):

        m = self.coords[0][1]
        for i in range(4):
            m = min(m, self.coords[i][1])

        return m

    def maxY(self):

        m = self.coords[0][1]
        for i in range(4):
            m = max(m, self.coords[i][1])

        return m

    def rotatedLeft(self):

        if self.pieceShape == TETROMINOES.square_shape:
            return self

        result = Shape()
        result.pieceShape = self.pieceShape

        for i in range(4):
            result.setX(i, self.y(i))
            result.setY(i, -self.x(i))

        return result

    def rotatedRight(self):

        if self.pieceShape == TETROMINOES.square_shape:
            return self

        result = Shape()
        result.pieceShape = self.pieceShape

        for i in range(4):
            result.setX(i, -self.y(i))
            result.setY(i, self.x(i))

        return result

def main():

    app = QtGui.QApplication(sys.argv)
    t = Tetris()
    t.show()
    t.raise_()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
