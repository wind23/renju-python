import re
import copy
from enum import Enum, IntEnum
from typing import List, Tuple, Union, Optional

# Semantic type aliases for coordinates and groups
Coordinate = Tuple[int, int]
StrCoordinate = Tuple[str, str]
CoordinateGroup = List[Coordinate]
CoordinateGroups = List[CoordinateGroup]
SymmetryResult = Tuple[CoordinateGroups, CoordinateGroups]
MoveList = List[List[int]]
from .check_forbid import get_foul_type


# Renju / Gomoku rule enum
# FREESTYLE: Free style rules (no forbid moves, overline counts as win)
# STANDARD: Standard rules (no forbid moves, overline does not win, only five-in-a-row wins)
# RENJU: Renju rules (Black has double-three, double-four, overline forbid moves; White has no forbids)
class Rule(IntEnum):
    FREESTYLE = 0
    STANDARD = 1
    RENJU = 4

    @classmethod
    def from_str(cls, rule_str: str) -> 'Rule':
        """
        Parse rule string into Rule enum, case-insensitively.
        """
        try:
            return cls[rule_str.upper()]
        except KeyError:
            raise ValueError(f"Rule '{rule_str}' is not valid. Choose from 'freestyle', 'standard', 'renju'.")


class BoardStatus(IntEnum):
    ONGOING = 0      # Game is not ended
    BLACK_WIN = 1    # Black wins
    WHITE_WIN = 2    # White wins
    DRAW = 3         # Draw (board full)


class WinReason(str, Enum):
    NORMAL = "normal"
    FIVE_IN_A_ROW = "five_in_a_row"   # Five-in-a-row (exactly 5 for standard/renju, 5+ for freestyle/white-renju)
    OVERLINE = "overline"             # Black overline forbid (or White overline win in freestyle)
    DOUBLE_FOUR = "double_four"       # Black double-four forbid
    DOUBLE_THREE = "double_three"     # Black double-three forbid
    DRAW = "draw"                     # Board full draw


PlayResult = Tuple[BoardStatus, WinReason]


def strxy_to_coordinate(pos_x: str, pos_y: str) -> Coordinate:
    """
    Convert string coordinates (e.g. 'h', '8') to 0-based integer coordinates (x, y).
    Supports Excel-style multi-character column names (e.g. 'a'->0, 'z'->25, 'aa'->26).
    """
    pos_x = pos_x.lower()
    x = 0
    for i in pos_x:
        x = x * 26 + ord(i) - ord('a') + 1
    x -= 1
    y = int(pos_y) - 1
    return (x, y)


def coordinate_to_strxy(x: int, y: int) -> StrCoordinate:
    """
    Convert 0-based integer coordinates (x, y) to string coordinate tuple (pos_x, pos_y).
    Example: (7, 7) -> ('h', '8')
    """
    x_val = int(x) + 1
    pos_x = ''
    while x_val > 0:
        last_num = (x_val - 1) % 26
        pos_x = chr(ord('a') + last_num) + pos_x
        x_val = (x_val - last_num) // 26
    pos_y = str(int(y) + 1)
    return (pos_x, pos_y)


class RenjuBoard:
    """
    Renju/Gomoku board representation to record and manage the move sequence.
    """

    rule: Rule
    _rule_name: str
    board_size: int
    moves: MoveList
    status: BoardStatus
    reason: WinReason

    def __init__(
        self,
        pos: str = '',
        moves: Optional[MoveList] = None,
        board_size: int = 15,
        rule: Union[str, Rule] = Rule.RENJU
    ) -> None:
        """
        Initialize the board.
        
        Args:
            pos: A concatenated string of move coordinates, e.g. "h8i9g7" or "h8, i9" (cleaned automatically)
            moves: A list/tuple of coordinate pairs, e.g. [[7, 7], [8, 8]]
            board_size: The grid size of the board, default 15
            rule: Rule type, selected from 'freestyle', 'standard', 'renju' or Rule enum
        """
        if isinstance(rule, str):
            self.rule = Rule.from_str(rule)
            self._rule_name = rule.lower()
        elif isinstance(rule, Rule):
            self.rule = rule
            self._rule_name = rule.name.lower()
        else:
            raise TypeError("Rule must be a string or a Rule enum member.")

        board_size = int(board_size)
        if board_size < 5:
            raise ValueError(f'Board size {board_size} is not valid.')
        self.board_size = board_size

        self.moves = []
        self.status = BoardStatus.ONGOING
        self.reason = WinReason.NORMAL

        if pos and moves:
            raise ValueError(
                'Parameters pos and moves cannot be used at the same time.')
        elif pos and not moves:
            # Clean string, preserving only alphanumeric characters
            cleaned_pos = ''.join(filter(str.isalnum, pos.lower()))
            # Extract 'pass' or (letters, numbers) pairs
            parsed_moves = re.findall(r'(pass)|([a-z]+)([1-9][0-9]*)', cleaned_pos)
            pos_len = 0
            for is_pass, pos_x, pos_y in parsed_moves:
                if is_pass == 'pass':
                    self.play_move(-1, -1)
                    pos_len += 4
                else:
                    x, y = strxy_to_coordinate(pos_x, pos_y)
                    self.play_move(x, y)
                    pos_len += len(pos_x) + len(pos_y)
            if pos_len != len(cleaned_pos):
                raise ValueError(f'Pos \'{pos}\' is not correct.')
        elif moves and not pos:
            for x, y in moves:
                self.play_move(int(x), int(y))

    def play_move(self, x: int, y: int) -> PlayResult:
        """
        Play a stone at coordinates (x, y). Validates bounds, occupancy, and game state.
        For a pass move, use (-1, -1).
        
        Args:
            x: Column index (0 to board_size-1, or -1 for pass)
            y: Row index (0 to board_size-1, or -1 for pass)
        """
        if self.status != BoardStatus.ONGOING:
            raise ValueError("Cannot play move: game has already ended.")

        # Handle pass move
        if x == -1 and y == -1:
            self._update_status_after_move(-1, -1)
            return self.status, self.reason

        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            raise ValueError(f'Move ({x}, {y}) is out of board boundaries.')
        
        # Check if already occupied
        if [x, y] in self.moves:
            raise ValueError(f'Move ({x}, {y}) is already occupied.')
            
        self._update_status_after_move(x, y)
        return self.status, self.reason

    def play_str(self, pos_str: str) -> PlayResult:
        """
        Append one or more moves via a coordinate string.
        Example: board.play_str("h8") or board.play_str("i9passj10")
        """
        cleaned = ''.join(filter(str.isalnum, pos_str.lower()))
        parsed = re.findall(r'(pass)|([a-z]+)([1-9][0-9]*)', cleaned)
        parsed_len = 0
        for is_pass, pos_x, pos_y in parsed:
            if is_pass == 'pass':
                self.play_move(-1, -1)
                parsed_len += 4
            else:
                x, y = strxy_to_coordinate(pos_x, pos_y)
                self.play_move(x, y)
                parsed_len += len(pos_x) + len(pos_y)
        if parsed_len != len(cleaned):
            raise ValueError(f'Pos string \'{pos_str}\' is not correct.')
        return self.status, self.reason


    def _update_status_after_move(self, x: int, y: int) -> None:
        """
        Private helper to play a move and update the board's status and win reason.
        """
        # Determine player (1 = Black, 2 = White)
        player = 1 if len(self.moves) % 2 == 0 else 2
        self.moves.append([x, y])

        # Handle pass move
        if x == -1 and y == -1:
            if len(self.moves) >= 2 and self.moves[-2] == [-1, -1]:
                self.status = BoardStatus.DRAW
                self.reason = WinReason.DRAW
            return

        # Build board grid representing the state after this move (ignoring pass moves)
        board_grid = [[0] * self.board_size for _ in range(self.board_size)]
        for index, (mx, my) in enumerate(self.moves):
            if mx == -1 and my == -1:
                continue
            board_grid[mx][my] = 1 if index % 2 == 0 else 2

        # Check consecutive stones count in 4 directions around (x, y)
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        max_consecutive = 1
        has_exactly_five = False

        for dx, dy in directions:
            # count forward
            forward_count = 0
            tx, ty = x + dx, y + dy
            while 0 <= tx < self.board_size and 0 <= ty < self.board_size and board_grid[tx][ty] == player:
                forward_count += 1
                tx += dx
                ty += dy

            # count backward
            backward_count = 0
            tx, ty = x - dx, y - dy
            while 0 <= tx < self.board_size and 0 <= ty < self.board_size and board_grid[tx][ty] == player:
                backward_count += 1
                tx -= dx
                ty -= dy

            consecutive = 1 + forward_count + backward_count
            if consecutive > max_consecutive:
                max_consecutive = consecutive
            if consecutive == 5:
                has_exactly_five = True

        game_ended = False

        if self.rule == Rule.FREESTYLE:
            if max_consecutive >= 5:
                self.status = BoardStatus.BLACK_WIN if player == 1 else BoardStatus.WHITE_WIN
                self.reason = WinReason.FIVE_IN_A_ROW
                game_ended = True

        elif self.rule == Rule.STANDARD:
            if has_exactly_five:
                self.status = BoardStatus.BLACK_WIN if player == 1 else BoardStatus.WHITE_WIN
                self.reason = WinReason.FIVE_IN_A_ROW
                game_ended = True

        elif self.rule == Rule.RENJU:
            if player == 2:  # White plays
                if max_consecutive >= 5:
                    self.status = BoardStatus.WHITE_WIN
                    self.reason = WinReason.FIVE_IN_A_ROW
                    game_ended = True
            else:  # Black plays
                if has_exactly_five:
                    # Black achieving exactly 5 wins immediately. Forbid checks are bypassed.
                    self.status = BoardStatus.BLACK_WIN
                    self.reason = WinReason.FIVE_IN_A_ROW
                    game_ended = True
                else:
                    # Check forbid (candidate evaluated with board grid excluding this move and passes)
                    board_grid_for_forbid = [[0] * self.board_size for _ in range(self.board_size)]
                    for index, (mx, my) in enumerate(self.moves[:-1]):
                        if mx == -1 and my == -1:
                            continue
                        board_grid_for_forbid[mx][my] = 1 if index % 2 == 0 else 2

                    foul = get_foul_type(board_grid_for_forbid, x, y)
                    if foul == 3:
                        self.status = BoardStatus.WHITE_WIN
                        self.reason = WinReason.OVERLINE
                        game_ended = True
                    elif foul == 2:
                        self.status = BoardStatus.WHITE_WIN
                        self.reason = WinReason.DOUBLE_FOUR
                        game_ended = True
                    elif foul == 1:
                        self.status = BoardStatus.WHITE_WIN
                        self.reason = WinReason.DOUBLE_THREE
                        game_ended = True

        # Count only non-pass moves to check if the board is full
        non_pass_count = sum(1 for mx, my in self.moves if mx != -1 and my != -1)
        if not game_ended and non_pass_count == self.board_size * self.board_size:
            self.status = BoardStatus.DRAW
            self.reason = WinReason.DRAW

    def undo(self) -> List[int]:
        """
        Undo: remove the last move and return its coordinates [x, y].
        Raises IndexError if the board is empty.
        """
        if not self.moves:
            raise IndexError("Cannot undo from an empty board.")
        last_move = self.moves.pop()
        
        # Recalculate status and reason by re-playing the moves
        self._recalculate_status()
        return last_move

    def _recalculate_status(self) -> None:
        """
        Recalculate status and reason from scratch using current self.moves.
        """
        all_moves = list(self.moves)
        self.moves = []
        self.status = BoardStatus.ONGOING
        self.reason = WinReason.NORMAL

        for x, y in all_moves:
            self._update_status_after_move(x, y)

    @property
    def current_player(self) -> str:
        """
        Get the current turn player.
        Black plays first, odd move counts mean it is White's turn.
        Returns: 'black' or 'white'
        """
        return 'white' if len(self.moves) % 2 != 0 else 'black'

    def __len__(self) -> int:
        """
        Return the total number of moves played so far.
        """
        return len(self.moves)

    def get_pos(self, separator: str = '') -> str:
        """
        Return the moves sequence formatted as a string.
        """
        strxys = []
        for x, y in self.moves:
            if x == -1 and y == -1:
                strxys.append("pass")
            else:
                pos_x, pos_y = coordinate_to_strxy(x, y)
                strxys.append(pos_x + pos_y)
        return separator.join(strxys)

    def get_moves(self) -> MoveList:
        """
        Return a deep copy of the coordinates of moves played.
        """
        return copy.deepcopy(self.moves)

    def __str__(self) -> str:
        """
        Return an aligned text representation of the current board grid.
        """
        # Build board grid
        grid = [['.'] * self.board_size for _ in range(self.board_size)]
        for index, (x, y) in enumerate(self.moves):
            if x == -1 and y == -1:
                continue
            # Even moves (0, 2, 4...) are Black ('X'), odd moves are White ('O')
            grid[y][x] = 'X' if index % 2 == 0 else 'O'

        lines = []
        # Column headers (a, b, c...)
        col_headers = []
        for x in range(self.board_size):
            pos_x, _ = coordinate_to_strxy(x, 0)
            col_headers.append(pos_x)
        
        # Calculate sizing padding for rows and columns alignment
        max_row_num_width = len(str(self.board_size))
        max_col_width = max(len(h) for h in col_headers)
        col_fmt = f"{{:>{max_col_width}}}"
        
        # Column headers row
        header_str = " " * (max_row_num_width + 1) + " ".join(col_fmt.format(h) for h in col_headers)
        lines.append(header_str)

        # Board grid rows (row numbers start from 1 to board_size)
        for y in range(self.board_size):
            row_num_str = f"{y + 1:>{max_row_num_width}}"
            row_cells = []
            for x in range(self.board_size):
                row_cells.append(col_fmt.format(grid[y][x]))
            lines.append(f"{row_num_str} " + " ".join(row_cells))

        return "\n".join(lines)

    def display(self) -> None:
        """
        Print the board representation to the standard output.
        """
        print(self.__str__())

    def copy(self) -> 'RenjuBoard':
        """
        Return a copy of the board (Identity transformation).
        """
        return RenjuBoard(moves=self.get_moves(), board_size=self.board_size, rule=self.rule)

    def flip_x(self) -> 'RenjuBoard':
        """
        Flip the board along the X-axis (vertical flip: y -> board_size - 1 - y).
        """
        n = self.board_size
        new_moves = [[x, n - 1 - y] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def flip_y(self) -> 'RenjuBoard':
        """
        Flip the board along the Y-axis (horizontal flip: x -> board_size - 1 - x).
        """
        n = self.board_size
        new_moves = [[n - 1 - x, y] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def flip_diagonal(self) -> 'RenjuBoard':
        """
        Flip the board along the main diagonal (top-left to bottom-right: x <-> y).
        """
        n = self.board_size
        new_moves = [[y, x] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def flip_anti_diagonal(self) -> 'RenjuBoard':
        """
        Flip the board along the anti-diagonal (bottom-left to top-right: x -> board_size - 1 - y, y -> board_size - 1 - x).
        """
        n = self.board_size
        new_moves = [[n - 1 - y, n - 1 - x] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def rotate_90(self) -> 'RenjuBoard':
        """
        Rotate the board 90 degrees clockwise (x -> board_size - 1 - y, y -> x).
        """
        n = self.board_size
        new_moves = [[n - 1 - y, x] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def rotate_90_ccw(self) -> 'RenjuBoard':
        """
        Rotate the board 90 degrees counter-clockwise (x -> y, y -> board_size - 1 - x).
        """
        n = self.board_size
        new_moves = [[y, n - 1 - x] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def rotate_180(self) -> 'RenjuBoard':
        """
        Rotate the board 180 degrees (x -> board_size - 1 - x, y -> board_size - 1 - y).
        """
        n = self.board_size
        new_moves = [[n - 1 - x, n - 1 - y] if (x != -1 or y != -1) else [-1, -1] for x, y in self.moves]
        return RenjuBoard(moves=new_moves, board_size=n, rule=self.rule)

    def __eq__(self, other: object) -> bool:
        """
        Check if two boards are exactly identical (same rule, size, and move sequence).
        """
        if not isinstance(other, RenjuBoard):
            return NotImplemented
        return (self.board_size == other.board_size and
                self.rule == other.rule and
                self.moves == other.moves)

    def is_symmetric_to(self, other: 'RenjuBoard') -> bool:
        """
        Check if this board is equivalent to another board under any of the 8 symmetry transformations.
        """
        if not isinstance(other, RenjuBoard):
            return False
        if self.board_size != other.board_size or self.rule != other.rule:
            return False

        # Try all 8 possible symmetry transformations
        transformations = [
            self.copy,
            self.flip_x,
            self.flip_y,
            self.flip_diagonal,
            self.flip_anti_diagonal,
            self.rotate_90,
            self.rotate_90_ccw,
            self.rotate_180
        ]
        return any(t() == other for t in transformations)

    def find_symmetric_candidates(
        self,
        candidates: List[Coordinate]
    ) -> SymmetryResult:
        """
        Find equivalent (symmetric) candidate moves among a list of coordinate tuples.
        Symmetry is invariant under rotation, reflection, and translation.
        
        Args:
            candidates: A list of candidate (x, y) coordinates.
            
        Returns:
            A tuple of (symmetric_groups, all_groups) where:
            - symmetric_groups: A list of lists of coordinate tuples that are symmetric to each other (size > 1).
            - all_groups: A list of lists containing all coordinates grouped by equivalence classes.
        """
        # Determine current player color (1 for Black, 2 for White)
        current_player_color = 1 if len(self.moves) % 2 == 0 else 2

        # 8 D4 transformations
        d4_transforms = [
            lambda x, y: (x, y),
            lambda x, y: (-x, y),
            lambda x, y: (x, -y),
            lambda x, y: (-x, -y),
            lambda x, y: (y, x),
            lambda x, y: (-y, x),
            lambda x, y: (y, -x),
            lambda x, y: (-y, -x)
        ]

        # Map frozenset signature to list of candidates
        signature_groups: dict = {}

        for candidate in candidates:
            # Gather all stones on the board plus the candidate
            stones = []
            for index, (mx, my) in enumerate(self.moves):
                if mx == -1 and my == -1:
                    continue
                color = 1 if index % 2 == 0 else 2
                stones.append((mx, my, color))
            stones.append((candidate[0], candidate[1], current_player_color))

            # Generate the 8 canonical forms
            canonical_views = []
            for transform in d4_transforms:
                transformed_stones = []
                for x, y, color in stones:
                    tx, ty = transform(x, y)
                    transformed_stones.append((tx, ty, color))

                # Shift minimum coordinates to 0 to eliminate translation offset
                min_x = min(s[0] for s in transformed_stones)
                min_y = min(s[1] for s in transformed_stones)

                canonical_stones = tuple(sorted(
                    (s[0] - min_x, s[1] - min_y, s[2]) for s in transformed_stones
                ))
                canonical_views.append(canonical_stones)

            # Invariant signature under D4 symmetry and translation
            signature = frozenset(canonical_views)

            if signature not in signature_groups:
                signature_groups[signature] = []
            signature_groups[signature].append(candidate)

        # Build output lists
        all_groups = list(signature_groups.values())
        symmetric_groups = [g for g in all_groups if len(g) > 1]

        return symmetric_groups, all_groups

    def to_sgf(
        self,
        black_name: str = "Black",
        white_name: str = "White",
        date: str = "",
        event: str = ""
    ) -> str:
        """
        Export the current board state and move history to SGF format.
        
        Args:
            black_name: Name of the black player.
            white_name: Name of the white player.
            date: Game date string (e.g. YYYY-MM-DD).
            event: Event name.
            
        Returns:
            The SGF string representation of the game.
        """
        re_val = ""
        if self.status == BoardStatus.BLACK_WIN:
            re_val = f"B+{self.reason.value}"
        elif self.status == BoardStatus.WHITE_WIN:
            re_val = f"W+{self.reason.value}"
        elif self.status == BoardStatus.DRAW:
            re_val = "Draw"

        root_props = [
            ("GM", "4"),  # Renju / Gomoku
            ("FF", "4"),  # SGF version 4
            ("SZ", str(self.board_size)),
            ("RU", self.rule.name.capitalize()),
            ("KM", "0.0"),
            ("PB", black_name),
            ("PW", white_name),
        ]
        if date:
            root_props.append(("DT", date))
        if event:
            root_props.append(("EV", event))
        if re_val:
            root_props.append(("RE", re_val))

        sgf = "(;"
        for key, val in root_props:
            escaped_val = val.replace("]", "\\]")
            sgf += f"{key}[{escaped_val}]"

        # Add moves
        for index, (x, y) in enumerate(self.moves):
            color_prefix = "B" if index % 2 == 0 else "W"
            if x == -1 and y == -1:
                sgf += f";{color_prefix}[]"
            else:
                col_char = chr(ord('a') + x)
                row_char = chr(ord('a') + y)
                sgf += f";{color_prefix}[{col_char}{row_char}]"

        sgf += ")"
        return sgf

    @classmethod
    def from_sgf(cls, sgf_content: str) -> 'RenjuBoard':
        """
        Parse an SGF string and reconstruct the RenjuBoard state.
        
        Args:
            sgf_content: The SGF file contents as a string.
            
        Returns:
            A reconstructed RenjuBoard instance.
        """
        content = sgf_content.strip()
        if not content.startswith('(') or not content.endswith(')'):
            raise ValueError("Invalid SGF format: must start with '(' and end with ')'")
        
        content = content[1:-1].strip()
        
        # Parse nodes split by ';' outside brackets
        nodes = []
        current_node_content = []
        in_brackets = False
        escaped = False
        
        for char in content:
            if escaped:
                current_node_content.append(char)
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '[':
                in_brackets = True
                current_node_content.append(char)
            elif char == ']':
                in_brackets = False
                current_node_content.append(char)
            elif char == ';' and not in_brackets:
                node_str = "".join(current_node_content).strip()
                if node_str:
                    nodes.append(node_str)
                current_node_content = []
            else:
                current_node_content.append(char)
        
        if current_node_content:
            node_str = "".join(current_node_content).strip()
            if node_str:
                nodes.append(node_str)
                
        if not nodes:
            raise ValueError("Invalid SGF format: no nodes found.")
            
        def parse_properties(node_str: str) -> dict:
            props = {}
            idx = 0
            n = len(node_str)
            while idx < n:
                while idx < n and not node_str[idx].isupper():
                    idx += 1
                if idx >= n:
                    break
                id_start = idx
                while idx < n and node_str[idx].isupper():
                    idx += 1
                prop_id = node_str[id_start:idx]
                
                values = []
                while idx < n and node_str[idx] == '[':
                    idx += 1
                    val_chars = []
                    escaped_in_val = False
                    while idx < n:
                        c = node_str[idx]
                        if escaped_in_val:
                            val_chars.append(c)
                            escaped_in_val = False
                            idx += 1
                        elif c == '\\':
                            escaped_in_val = True
                            idx += 1
                        elif c == ']':
                            idx += 1
                            break
                        else:
                            val_chars.append(c)
                            idx += 1
                    values.append("".join(val_chars))
                props[prop_id] = values
            return props

        root_props = parse_properties(nodes[0])
        
        sz_val = root_props.get("SZ", ["15"])[0]
        board_size = int(sz_val)
        
        ru_val = root_props.get("RU", ["Renju"])[0]
        rule = Rule.from_str(ru_val)
        
        board = cls(board_size=board_size, rule=rule)
        
        for node in nodes[1:]:
            props = parse_properties(node)
            move_val = None
            if "B" in props:
                move_val = props["B"][0]
            elif "W" in props:
                move_val = props["W"][0]
                
            if move_val is not None:
                if move_val == "" or move_val == "tt":
                    board.play_move(-1, -1)
                else:
                    if len(move_val) != 2:
                        raise ValueError(f"Invalid SGF coordinate value: {move_val}")
                    col_char, row_char = move_val[0], move_val[1]
                    x = ord(col_char.lower()) - ord('a')
                    y = ord(row_char.lower()) - ord('a')
                    board.play_move(x, y)
                    
        return board







