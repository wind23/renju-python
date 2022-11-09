import re
import copy

rule_dict = {'freestyle': 0, 'standard': 1, 'renju': 4}


def strxy_to_coordinate(pos_x, pos_y):
    pos_x = pos_x.lower()
    x = 0
    for i in pos_x:
        x = x * 26 + ord(i) - ord('a') + 1
    x -= 1
    y = int(pos_y) - 1
    return (x, y)


def coordinate_to_strxy(x, y):
    x = int(x) + 1
    pos_x = ''
    while x > 0:
        last_num = (x - 1) % 26
        pos_x = chr(ord('a') + last_num) + pos_x
        x = (x - last_num) // 26
    pos_y = str(int(y) + 1)
    return (pos_x, pos_y)


class RenjuBoard:

    def __init__(self, pos='', moves=None, board_size=15, rule='renju'):
        if not rule in rule_dict.keys():
            raise ValueError(f'Rule \'{rule}\' is not valid.')
        self.rule = rule_dict[rule]
        board_size = int(board_size)
        if board_size < 5:
            raise ValueError(f'Board size {board_size} is not valid.')
        self.board_size = board_size

        self.moves = []
        if pos and moves:
            raise ValueError(
                'Parameters pos and moves cannot be used at the same time.')
        elif pos and not moves:
            pos = ''.join(filter(str.isalnum, pos.lower()))
            moves = re.findall(r'([a-z]+)([1-9][0-9]*)', pos)
            pos_len = 0
            for pos_x, pos_y in moves:
                x, y = strxy_to_coordinate(pos_x, pos_y)
                if 0 <= x < self.board_size and 0 <= y < self.board_size and not [
                        x, y
                ] in self.moves:
                    self.moves.append([x, y])
                else:
                    raise ValueError(f'Move ({x}, {y}) is not correct.')
                pos_len += len(pos_x) + len(pos_y)
            if pos_len != len(pos):
                raise ValueError(f'Pos \'{pos}\' is not correct.')
        elif moves and not pos:
            for x, y in moves:
                x = int(x)
                y = int(y)
                if 0 <= x < self.board_size and 0 <= y < self.board_size and not [
                        x, y
                ] in self.moves:
                    self.moves.append([x, y])
                else:
                    raise ValueError(f'Move ({x}, {y}) is not correct.')

    def get_pos(self, separator=''):
        strxys = []
        for x, y in self.moves:
            pos_x, pos_y = coordinate_to_strxy(x, y)
            strxys.append(pos_x + pos_y)
        return separator.join(strxys)

    def get_moves(self):
        return copy.deepcopy(self.moves)
