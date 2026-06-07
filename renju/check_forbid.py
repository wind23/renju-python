import copy
from typing import List

class ForbidChecker:
    """
    Thread-safe checker for Renju forbidden moves (double-three, double-four, and overline for Black).
    Ported and cleaned from Piskvork judge implementation to avoid global variables.
    """

    class Line:
        def __init__(self) -> None:
            self.x: List[int] = []
            self.p: int = 0

        def setline(self, a: List[int], p: int) -> None:
            a[2 + p] = 1  # temporarily assign Black stone (value 1)
            self.x = a[2:]
            self.p = p

        def A6(self, n: int) -> int:
            x = self.x
            p = self.p
            for i in range(max(p - 5, 0), min(p, n - 6) + 1):
                if x[i] + x[i + 1] + x[i + 2] + x[i + 3] + x[i + 4] + x[i + 5] == 6:
                    return 1
            return 0

        def A5(self, n: int) -> int:
            x = self.x
            p = self.p
            for i in range(max(p - 4, 0), min(p, n - 5) + 1):
                if (
                    x[i] + x[i + 1] + x[i + 2] + x[i + 3] + x[i + 4] == 5
                    and x[i - 1] != 1
                    and x[i + 5] != 1
                ):
                    return 1
            return 0

        def B4(self, n: int) -> int:
            x = self.x
            p = self.p
            for i in range(max(p - 4, 0), min(p, n - 5) + 1):
                if (
                    x[i] + x[i + 1] + x[i + 2] + x[i + 3] + x[i + 4] == 4
                    and x[i - 1] != 1
                    and x[i + 5] != 1
                ):
                    if x[i + 4] == 0:
                        return 1
                    elif x[i + 3] == 0:
                        if (
                            p == i + 4
                            and x[i + 5] == 0
                            and x[i + 6] == 1
                            and x[i + 7] == 1
                            and x[i + 8] == 1
                            and x[i + 9] != 1
                        ):
                            return 2
                        return 1
                    elif x[i + 2] == 0:
                        if (
                            (p == i + 4 or p == i + 3)
                            and x[i + 5] == 0
                            and x[i + 6] == 1
                            and x[i + 7] == 1
                            and x[i + 8] != 1
                        ):
                            return 2
                        return 1
                    elif x[i + 1] == 0:
                        if (x[i + 5] == 0 and x[i + 6] == 1 and x[i + 7] != 1) and (
                            p == i + 4 or p == i + 3 or p == i + 2
                        ):
                            return 2
                        return 1
                    else:
                        return 1
            return 0

        def A3(self, n: int) -> int:
            x = self.x
            p = self.p
            for i in range(max(p - 3, 0), min(p, n - 4) + 1):
                if (
                    x[i] + x[i + 1] + x[i + 2] + x[i + 3] == 3
                    and x[i - 1] == 0
                    and x[i - 2] != 1
                ):
                    if x[i + 3] == 0:
                        if x[i + 4] != 1:
                            if x[i - 2] == 0 and x[i - 3] != 1:
                                if x[i + 4] == 0 and x[i + 5] != 1:
                                    return (0x10000 | ((i - 1) << 8) | (i + 3))
                                return (0x100 | (i - 1))
                            if x[i + 4] == 0 and x[i + 5] != 1:
                                return (0x100 | (i + 3))
                    elif x[i + 2] == 0:
                        if x[i + 4] == 0 and x[i + 5] != 1:
                            return (0x100 | (i + 2))
                    elif x[i + 1] == 0:
                        if x[i + 4] == 0 and x[i + 5] != 1:
                            return (0x100 | (i + 1))
            return 0

    def __init__(self, board: List[List[int]], x: int, y: int) -> None:
        self.board = board
        self.N = len(board)
        self.X = x
        self.Y = y

        self.x1 = [[0 for _ in range(self.N + 4)] for _ in range(self.N)]
        self.x2 = [[0 for _ in range(self.N + 4)] for _ in range(self.N)]
        self.x3 = [[0 for _ in range(self.N + 4)] for _ in range(2 * self.N - 1)]
        self.x4 = [[0 for _ in range(self.N + 4)] for _ in range(2 * self.N - 1)]

        self.pad(self.x1, self.N, self.N)
        self.pad(self.x2, self.N, self.N)
        self.pad(self.x3, 2 * self.N - 1, 0)
        self.pad(self.x4, 2 * self.N - 1, 0)

        for i in range(self.N):
            for j in range(self.N):
                val = 0
                if board[i][j] == 1:
                    val = 1
                elif board[i][j] == 2:
                    val = -1
                self.x1[i][j + 2] = val
                self.x2[j][i + 2] = val
                self.x3[i + j][j + 2] = val
                self.x4[self.N - 1 - j + i][self.N - 1 - j + 2] = val

        self.l1 = self.Line()
        self.l2 = self.Line()
        self.l3 = self.Line()
        self.l4 = self.Line()

    def pad(self, x: List[List[int]], c: int, l: int) -> None:
        for i in range(c):
            x[i][0] = x[i][1] = 20
            for j in range(l, self.N + 2):
                x[i][j + 2] = 20

    def A3(self, l: Line, f) -> bool:
        r = l.A3(self.N)
        return bool(r and (not f(r & 0xFF) or (r >= 0x10000 and not f((r >> 8) & 0xFF))))

    def foulr(self, x: int, y: int, five: int) -> int:
        result = 0
        if self.x1[x][y + 2] != -1:
            m1 = copy.deepcopy(self.l1)
            m2 = copy.deepcopy(self.l2)
            m3 = copy.deepcopy(self.l3)
            m4 = copy.deepcopy(self.l4)
            x0, y0 = self.X, self.Y
            self.X, self.Y = x, y
            sign = self.x1[x][y + 2]

            self.l1.setline(self.x1[x], y)
            self.l2.setline(self.x2[y], x)
            self.l3.setline(self.x3[x + y], y)
            self.l4.setline(self.x4[self.N - 1 - y + x], self.N - 1 - y)

            f1 = lambda r: self.foulr(self.X, r, 1)
            f2 = lambda r: self.foulr(r, self.Y, 1)
            f3 = lambda r: self.foulr(self.X + self.Y - r, r, 1)
            f4 = lambda r: self.foulr(self.N - 1 + self.X - self.Y - r, self.N - 1 - r, 1)

            # Priority of forbidden moves: Overline (3) > Double-four (2) > Double-three (1)
            if self.l1.A5(self.N) == 1 or self.l2.A5(self.N) == 1 or self.l3.A5(self.N) == 1 or self.l4.A5(self.N) == 1:
                result = five
            elif self.l1.A6(self.N) == 1 or self.l2.A6(self.N) == 1 or self.l3.A6(self.N) == 1 or self.l4.A6(self.N) == 1:
                result = 3  # Overline
            elif self.l1.B4(self.N) + self.l2.B4(self.N) + self.l3.B4(self.N) + self.l4.B4(self.N) >= 2:
                result = 2  # Double-four
            elif self.A3(self.l1, f1) + self.A3(self.l2, f2) + self.A3(self.l3, f3) + self.A3(self.l4, f4) >= 2:
                result = 1  # Double-three

            self.x1[x][y + 2] = self.x2[y][x + 2] = self.x3[x + y][y + 2] = self.x4[self.N - 1 - y + x][
                self.N - 1 - y + 2
            ] = sign
            self.l1 = m1
            self.l2 = m2
            self.l3 = m3
            self.l4 = m4
            self.X, self.Y = x0, y0
        return result

    def get_foul_type(self) -> int:
        return self.foulr(self.X, self.Y, 0)


def get_foul_type(board: List[List[int]], x: int, y: int) -> int:
    """
    Check if playing Black at (x, y) is a foul / forbidden move.
    Returns:
        0: No foul
        1: Double-three (三三禁手)
        2: Double-four (四四禁手)
        3: Overline (长连禁手)
    """
    checker = ForbidChecker(board, x, y)
    return checker.get_foul_type()
