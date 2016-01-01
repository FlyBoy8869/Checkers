import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QWidget


checkers = []

red_square = QtGui.QColor(102, 0, 0, 255)
black_square = QtGui.QColor(0, 0, 0, 255)


class Checker(object):

    def __init__(self, x=0, y=0, color="black", image=None, crowned=None):
        self.x = x
        self.y = y
        self.color = color
        self.image = image
        self.image_crowned = crowned
        self.image_to_draw = image
        self.is_king = False

    def draw(self, qp):
        offset = 13
        qp.drawPixmap(QtCore.QPoint(self.x + offset, self.y + offset), self.image_to_draw)

    def king_me(self):
        self.is_king = True
        self.image_to_draw = self.image_crowned

    def __repr__(self):
        return "Checker({!r}, {!r}, {!r}, {!r}, {!r}".format(self.x, self.y, self.color, self.image, self.image_crowned)

    def __str__(self):
        return "Checker: x={!r}, y={!r}, color={!r}".format(self.x, self.y, self.color)


class Board(QWidget):

    SQUARE = 75

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setFixedSize(Board.SQUARE * 8 + 3, Board.SQUARE * 8 + 3)

        self.remainder = 0
        self.moving_checker = None
        self.starting_row = -1
        self.starting_col = -1
        self.ending_row = -1
        self.ending_col = -1
        self.current_row = - 1
        self.current_col = - 1
        self.jump_made = False
        self.valid_move = False

        self.checker_black = QtGui.QPixmap("images/checker_black_nv_50x50.png")
        self.image_crown_black = QtGui.QPixmap("images/checker_black_nv_crowned_50x50.png")
        self.checker_red = QtGui.QPixmap("images/checker_crab-1_50x50.png")
        self.image_crown_red = QtGui.QPixmap("images/checker_crab-1_crowned_50x50.png")

        self.i_checker_black = self.checker_black
        self.i_checker_red = self.checker_red

        self.board = self._setup_board()

        self.show()

    def paintEvent(self, event=None):
        qp = QtGui.QPainter(self)
        self.draw_board(qp)

        for checker in checkers:
            checker.draw(qp)

        if self.moving_checker:
            self.moving_checker.draw(qp)

    def draw_board(self, qp):
        save_pen = qp.pen()
        pen = QtGui.QPen(QtGui.QColor(255, 0, 0, 255))
        pen.setWidth(3)
        qp.setPen(pen)

        for row in range(8):
            for col in range(8):
                x_offset = row * Board.SQUARE + 1
                y_offset = col * Board.SQUARE + 1
                rect = QtCore.QRect(x_offset, y_offset, Board.SQUARE, Board.SQUARE)
                qp.drawRect(rect)
                color = red_square if col % 2 == self.remainder else black_square
                rect = QtCore.QRect(x_offset + 1, y_offset + 1, Board.SQUARE - 1, Board.SQUARE - 1)
                qp.fillRect(rect, color)

            self.remainder = 1 if self.remainder == 0 else 0

        qp.setPen(save_pen)

    def mousePressEvent(self, me):
        row, col = self._calc_row_col(me.x(), me.y())
        ulx = col * 75
        uly = row * 75
        lrx = col * 75 + 74
        lry = row * 75 + 74

        for checker in checkers:
            if ulx <= checker.x <= lrx and uly <= checker.y <= lry:
                self.moving_checker = checker
                print(checker)
                self.starting_row = row
                self.starting_col = col

    def mouseMoveEvent(self, me):
        if self.moving_checker:
            self.current_row, self.current_col = self._calc_row_col(me.x(), me.y())
            print("x={}, y={}, row={}, col= {}".format(me.x(), me.y(), self.current_row, self.current_col))

            self.moving_checker.x = me.x() - 25 - 10
            self.moving_checker.y = me.y() - 25 - 10
            self.update()

    def mouseReleaseEvent(self, me):
        self.ending_row, self.ending_col = self._calc_row_col(me.x(), me.y())
        row_delta, col_delta = self.distance()
        square_color = self.board[self.ending_row][self.ending_col]

        if 0 < row_delta <= 2 and 0 < col_delta <= 2 and (square_color != "red"):
            if self.moving_checker.color == "black" and self.down():
                self.valid_move = True
                if self.ending_row == 7:
                    self.moving_checker.king_me()
            elif self.moving_checker.is_king:
                self.valid_move = True

            if self.moving_checker.color == "red" and self.up():
                self.valid_move = True
                if self.ending_row == 0:
                    self.moving_checker.king_me()
            elif self.moving_checker.is_king:
                self.valid_move = True

        if self.moving_checker and self.valid_move:
            x = self.ending_col * Board.SQUARE
            y = self.ending_row * Board.SQUARE
            self.moving_checker.x = x
            self.moving_checker.y = y
        else:
            x = self.starting_col * Board.SQUARE
            y = self.starting_row * Board.SQUARE
            self.moving_checker.x = x
            self.moving_checker.y = y
        self.update()

        self.moving_checker = None
        self.valid_move = False

    def _calc_row_col(self, x, y):
        col = int(x / Board.SQUARE)
        row = int(y / Board.SQUARE)
        return row, col

    def _is_square_occupied(self):
        for checker in checkers:
            if checker.row == self.current_row and checker.col == self.current_col:
                return True

        return False

    def _setup_board(self):
        board = []

        for x in range(4):
            board.append(["red" if i % 2 == 0 else "black" for i in range(8)])
            board.append(["black" if i % 2 == 0 else "red" for i in range(8)])

        self._place_checkers()

        return board

    def _place_checkers(self):
        black_positions = [(0, 1), (0, 3), (0, 5), (0, 7),
                           (1, 0), (1, 2), (1, 4), (1, 6),
                           (2, 1), (2, 3), (2, 5), (2, 7)]

        red_positions = [(7, 0), (7, 2), (7, 4), (7, 6),
                         (6, 1), (6, 3), (6, 5), (6, 7),
                         (5, 0), (5, 2), (5, 4), (5, 6)]

        for row, col in black_positions:
            x = col * 75
            y = row * 75
            checkers.append(Checker(x, y, "black", self.i_checker_black, self.image_crown_black))

        for row, col in red_positions:
            x = col * 75
            y = row * 75
            checkers.append(Checker(x, y, "red", self.i_checker_red, self.image_crown_red))

    @staticmethod
    def find_checker(row, col, chkers):
        for checker in chkers:
            if checker.row == row and checker.col == col:
                return checker

        return None

    def left(self):
        if self.starting_col > self.ending_col:
            return True

        return False

    def right(self):
        if self.starting_col < self.ending_col:
            return True

        return False

    def up(self):
        if self.starting_row > self.ending_row:
            return True

        return False

    def down(self):
        if self.starting_row < self.ending_row:
            return True

        return False

    @staticmethod
    def jumped(starting_row, starting_col, ending_row, ending_col):

        row_delta, col_delta = Board.distance(starting_row, starting_col, ending_row, ending_col)

        if row_delta == 2 or col_delta == 2:
            if Board.up():
                t_row = starting_row - 1
            else:
                t_row = starting_row + 1

            if Board.left(starting_col, ending_col):
                t_col = starting_col - 1
            else:
                t_col = starting_col + 1

    def distance(self):
        return abs(self.starting_row - self.ending_row), abs(self.starting_col - self.ending_col)


def main():
    app = QtGui.QApplication(sys.argv)
    board = Board()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
