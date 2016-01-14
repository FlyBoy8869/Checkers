import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QWidget


checkers = []

red_square = QtGui.QColor(102, 0, 0, 255)
black_square = QtGui.QColor(0, 0, 0, 255)


class Checker(object):

    def __init__(self, x=0, y=0, color="black", image=None, crowned=None, invalid=None):
        self.x = x
        self.y = y
        self.color = color
        self.image = image
        self.image_crowned = crowned
        self.image_invalid = invalid
        self.image_to_draw = image
        self.is_king = False

    def draw(self, qp):
        offset = 13
        qp.drawPixmap(QtCore.QPoint(self.x + offset, self.y + offset), self.image_to_draw)

    def king_me(self):
        self.is_king = True
        self.set_image(self.image_crowned)

    def set_image(self, image):
        self.image_to_draw = image

    def set_invalid(self):
        self.set_image(self.image_invalid)

    def set_valid(self):
        self.set_image(self.image)

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
        self.checker_invalid = QtGui.QPixmap("images/invalid_50x50.png")
        self.checker_red = QtGui.QPixmap("images/checker_crab-1_50x50.png")
        self.image_crown_red = QtGui.QPixmap("images/checker_crab-1_crowned_50x50.png")

        self.i_checker_black = self.checker_black
        self.i_checker_red = self.checker_red

        self.board = self._setup_board()
        self._place_checkers()

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
        checker = self.find_checker(row, col, checkers)
        if checker:
            self.moving_checker = checker
            print(checker)
            self.starting_row = row
            self.starting_col = col

    def mouseMoveEvent(self, me):
        if self.moving_checker:
            self.current_row, self.current_col = self._calc_row_col(me.x(), me.y())
            row_delta, col_delta = self.distance(self.starting_row, self.starting_col,
                                                 self.current_row, self.current_col)
            square_taken = self._is_square_taken(self.current_row, self.current_col)
            square_color = self.board[self.current_row][self.current_col]
            not_starting_square = (self.current_row != self.starting_row) or (self.current_col != self.starting_col)
            if self.current_row == self.starting_row and self.current_col == self.starting_col:
                self.moving_checker.set_valid()
            elif not self._is_valid_move(row_delta, col_delta, square_color, square_taken) and not_starting_square:
                self.moving_checker.set_invalid()
            else:
                jumped_checker = self.get_jumped_checker(self.starting_row, self.starting_col, self.current_row, self.current_col)
                if row_delta == 2 and jumped_checker is None or (self.moving_checker.color == "black" and self.up() and not self.moving_checker.is_king):
                    print("mouseMoveEvent: row_delta = {}, jumped checker = {}".format(row_delta, jumped_checker))
                    self.moving_checker.set_invalid()
                else:
                    self.moving_checker.set_valid()
            # print("x={}, y={}, row={}, col= {}".format(me.x(), me.y(), self.current_row, self.current_col))

            self.moving_checker.x = me.x() - 25 - 10
            self.moving_checker.y = me.y() - 25 - 10
            self.update()

    def mouseReleaseEvent(self, me):
        self.ending_row, self.ending_col = self._calc_row_col(me.x(), me.y())
        if (0 > self.ending_row) or (self.ending_row > 7)\
                or (0 > self.ending_col) or (self.ending_col > 7):
            self.move_checker(self.starting_row, self.starting_col)
            self.update()
            return

        square_color = self.board[self.ending_row][self.ending_col]
        is_square_taken = self._is_square_taken(self.ending_row, self.ending_col)
        row_delta, col_delta = self.distance(self.starting_row, self.starting_col,
                                             self.ending_row, self.ending_col)

        if self.moving_checker is not None:
            if 0 < row_delta <= 2 and 0 < col_delta <= 2 and square_color != "red" and not is_square_taken:
                color = self.moving_checker.color
                # this enforces non-king forward jumps
                if row_delta == 2 and ((color == "black" and self.down()) or (color == "red" and self.up())):
                    checker = self.get_jumped_checker(self.starting_row, self.starting_col,
                                                      self.ending_row, self.ending_col)
                    if checker and checker.color != self.moving_checker.color:
                        self.valid_move = True
                        checkers.remove(checker)
                # this handles kings jumping forwards or backwards
                elif row_delta == 2 and self.moving_checker.is_king:
                    checker = self.get_jumped_checker(self.starting_row, self.starting_col,
                                                      self.ending_row, self.ending_col)
                    if checker and checker.color != self.moving_checker.color:
                        self.valid_move = True
                        checkers.remove(checker)
                # this handles single square movement
                elif ((color == "black" and self.down()) or (color == "red" and self.up())) or self.moving_checker.is_king:
                    self.valid_move = True

                if (self.ending_row == 0 or self.ending_row == 7) and not self.moving_checker.is_king:
                    self.moving_checker.king_me()

            if self.valid_move:
                self.move_checker(self.ending_row, self.ending_col)
            else:
                self.moving_checker.set_valid()
                self.move_checker(self.starting_row, self.starting_col)
            self.update()

            self.moving_checker = None
            self.valid_move = False

    def move_checker(self, row, col):
        self.moving_checker.x = col * Board.SQUARE
        self.moving_checker.y = row * Board.SQUARE

    def _calc_row_col(self, x, y):
        col = int(x / Board.SQUARE)
        row = int(y / Board.SQUARE)
        return row, col

    def _is_square_taken(self, row, col):
        for checker in checkers:
            checker_row, checker_col = self._calc_row_col(checker.x, checker.y)
            if checker_row == row and checker_col == col and checker is not self.moving_checker:
                return True
        return False

    def _is_valid_move(self, rd, cd, sc, st):
        if 0 < rd <= 2 and 0 < cd <= 2 and sc != "red" and not st:
            return True

        return False

    def _setup_board(self):
        board = []

        for x in range(4):
            board.append(["red" if i % 2 == 0 else "black" for i in range(8)])
            board.append(["black" if i % 2 == 0 else "red" for i in range(8)])

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
            checkers.append(Checker(x, y, "black", self.i_checker_black, self.image_crown_black, self.checker_invalid))

        for row, col in red_positions:
            x = col * 75
            y = row * 75
            checkers.append(Checker(x, y, "red", self.i_checker_red, self.image_crown_red, self.checker_invalid))

    def find_checker(self, row, col, chkers):
        for checker in chkers:
            checker_row, checker_col = self._calc_row_col(checker.x, checker.y)
            if checker_row == row and checker_col == col and checker is not self.moving_checker:
                return checker

        return None

    def get_jumped_checker(self, starting_row, starting_col, ending_row, ending_col):
        if self.down(starting_row, ending_row):
            t_row = ending_row - 1
            t_col = ending_col + 1 if self.left(starting_col, ending_col) else ending_col - 1
        elif self.up(starting_row, ending_row):
            t_row = ending_row + 1
            t_col = ending_col + 1 if self.left(starting_col, ending_col) else ending_col - 1
        else:
            return None

        return self.find_checker(t_row, t_col, checkers)

    def left(self, *args):
        if len(args):
            return True if args[0] > args[1] else False
        else:
            return True if self.starting_col > self.ending_col else False

    def right(self, *args):
        if len(args):
            return True if args[0] < args[1] else False
        else:
            return True if self.starting_col < self.ending_col else False

    def up(self, *args):
        if len(args):
            return True if args[0] > args[1] else False
        else:
            return True if self.starting_row > self.ending_row else False

    def down(self, *args):
        if len(args):
            return True if args[0] < args[1] else False
        else:
            return True if self.starting_row < self.ending_row else False

    def distance(self, starting_row, starting_col, ending_row, ending_col):
        return abs(starting_row - ending_row), abs(starting_col - ending_col)


def main():
    app = QtGui.QApplication(sys.argv)
    board = Board()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
