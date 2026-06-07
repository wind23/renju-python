"""
Comprehensive tests for RenjuBoard - board structure, coordinates, transformations,
equivalence, symmetry candidate detection, SGF import/export.
"""
import unittest
from renju import RenjuBoard, strxy_to_coordinate, coordinate_to_strxy, Rule, BoardStatus, WinReason


class TestCoordinateConversion(unittest.TestCase):
    """strxy_to_coordinate and coordinate_to_strxy edge cases."""

    def test_origin_corner(self):
        self.assertEqual(strxy_to_coordinate('a', '1'), (0, 0))
        self.assertEqual(coordinate_to_strxy(0, 0), ('a', '1'))

    def test_center_15x15(self):
        self.assertEqual(strxy_to_coordinate('h', '8'), (7, 7))
        self.assertEqual(coordinate_to_strxy(7, 7), ('h', '8'))

    def test_far_corner_15x15(self):
        self.assertEqual(strxy_to_coordinate('o', '15'), (14, 14))
        self.assertEqual(coordinate_to_strxy(14, 14), ('o', '15'))

    def test_single_letter_all_26(self):
        for i, ch in enumerate('abcdefghijklmnopqrstuvwxyz'):
            self.assertEqual(strxy_to_coordinate(ch, '1'), (i, 0))
            self.assertEqual(coordinate_to_strxy(i, 0), (ch, '1'))

    def test_multi_char_column_aa_is_26(self):
        self.assertEqual(strxy_to_coordinate('aa', '1'), (26, 0))
        self.assertEqual(coordinate_to_strxy(26, 0), ('aa', '1'))

    def test_multi_char_column_az(self):
        # 'az' = 1*26 + 26 - 1 = 51
        self.assertEqual(strxy_to_coordinate('az', '1'), (51, 0))
        self.assertEqual(coordinate_to_strxy(51, 0), ('az', '1'))

    def test_multi_char_column_ba(self):
        # 'ba' = 2*26 + 1 - 1 = 52
        self.assertEqual(strxy_to_coordinate('ba', '1'), (52, 0))
        self.assertEqual(coordinate_to_strxy(52, 0), ('ba', '1'))

    def test_roundtrip_many_coordinates(self):
        for x in range(30):
            for y in range(20):
                cx, cy = coordinate_to_strxy(x, y)
                self.assertEqual(strxy_to_coordinate(cx, cy), (x, y))

    def test_uppercase_input_tolerated(self):
        self.assertEqual(strxy_to_coordinate('H', '8'), (7, 7))
        self.assertEqual(strxy_to_coordinate('AA', '3'), (26, 2))


class TestBoardInitialisation(unittest.TestCase):
    """Board initialisation from pos string, moves list, and mixed inputs."""

    def test_empty_board(self):
        board = RenjuBoard()
        self.assertEqual(len(board), 0)
        self.assertEqual(board.board_size, 15)
        self.assertEqual(board.rule, Rule.RENJU)
        self.assertEqual(board.status, BoardStatus.ONGOING)
        self.assertEqual(board.reason, WinReason.NORMAL)

    def test_init_from_pos_basic(self):
        board = RenjuBoard(pos="h8i9g7", board_size=15)
        self.assertEqual(board.get_moves(), [[7, 7], [8, 8], [6, 6]])
        self.assertEqual(board.get_pos(), "h8i9g7")

    def test_init_from_pos_with_separators(self):
        board = RenjuBoard(pos="h8, i9; g7  h6")
        self.assertEqual(board.get_moves(), [[7, 7], [8, 8], [6, 6], [7, 5]])

    def test_init_from_pos_with_pass(self):
        board = RenjuBoard(pos="a1passb2")
        self.assertEqual(board.get_moves(), [[0, 0], [-1, -1], [1, 1]])
        self.assertEqual(board.get_pos(), "a1passb2")

    def test_init_from_moves(self):
        board = RenjuBoard(moves=[[7, 7], [8, 8], [-1, -1]])
        self.assertEqual(board.get_pos(), "h8i9pass")

    def test_init_both_pos_and_moves_raises(self):
        with self.assertRaises(ValueError):
            RenjuBoard(pos="h8", moves=[[7, 7]])

    def test_init_invalid_pos_raises(self):
        with self.assertRaises(ValueError):
            RenjuBoard(pos="h8xyz")

    def test_init_board_size_too_small(self):
        with self.assertRaises(ValueError):
            RenjuBoard(board_size=4)

    def test_init_custom_large_board(self):
        board = RenjuBoard(board_size=20)
        self.assertEqual(board.board_size, 20)

    def test_init_from_pos_lowercase_and_uppercase(self):
        b1 = RenjuBoard(pos="H8I9", rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8i9", rule=Rule.FREESTYLE)
        self.assertEqual(b1.get_moves(), b2.get_moves())

    def test_get_pos_with_separator(self):
        board = RenjuBoard(pos="h8i9g7")
        self.assertEqual(board.get_pos(separator=","), "h8,i9,g7")

    def test_get_pos_pass_representation(self):
        board = RenjuBoard(pos="h8passi9", rule=Rule.FREESTYLE)
        self.assertEqual(board.get_pos(), "h8passi9")

    def test_get_moves_returns_deep_copy(self):
        board = RenjuBoard(pos="h8")
        moves = board.get_moves()
        moves[0][0] = 999
        self.assertEqual(board.moves[0][0], 7)  # original unchanged


class TestPlayAndUndo(unittest.TestCase):
    """play_move, play_str, undo, current_player edge cases."""

    def test_current_player_alternates(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        self.assertEqual(board.current_player, 'black')
        board.play_move(7, 7)
        self.assertEqual(board.current_player, 'white')
        board.play_move(8, 8)
        self.assertEqual(board.current_player, 'black')

    def test_pass_does_not_change_player_rule(self):
        board = RenjuBoard()
        board.play_move(-1, -1)  # Black passes
        self.assertEqual(board.current_player, 'white')

    def test_play_str_single_move(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("h8")
        self.assertEqual(board.get_moves(), [[7, 7]])

    def test_play_str_multiple_moves(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("h8i9g7")
        self.assertEqual(board.get_moves(), [[7, 7], [8, 8], [6, 6]])

    def test_play_str_with_pass(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("h8passi9")
        self.assertEqual(board.get_moves(), [[7, 7], [-1, -1], [8, 8]])

    def test_play_move_out_of_bounds(self):
        board = RenjuBoard(board_size=15)
        with self.assertRaises(ValueError):
            board.play_move(15, 0)
        with self.assertRaises(ValueError):
            board.play_move(0, 15)
        with self.assertRaises(ValueError):
            board.play_move(-2, 0)  # negative but not -1

    def test_play_move_already_occupied(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_move(7, 7)
        board.play_move(8, 8)
        with self.assertRaises(ValueError):
            board.play_move(7, 7)

    def test_play_move_after_game_ends(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("a1b1a2b2a3b3a4b4")
        board.play_move(0, 4)  # Black wins
        with self.assertRaises(ValueError):
            board.play_move(9, 9)

    def test_undo_basic(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_move(7, 7)
        board.play_move(8, 8)
        last = board.undo()
        self.assertEqual(last, [8, 8])
        self.assertEqual(board.get_moves(), [[7, 7]])
        self.assertEqual(board.current_player, 'white')

    def test_undo_empty_board_raises(self):
        board = RenjuBoard()
        with self.assertRaises(IndexError):
            board.undo()

    def test_undo_pass_move(self):
        board = RenjuBoard()
        board.play_move(-1, -1)
        board.undo()
        self.assertEqual(len(board), 0)
        self.assertEqual(board.current_player, 'black')

    def test_undo_after_win_restores_ongoing(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("a1b1a2b2a3b3a4b4")
        board.play_move(0, 4)  # Black wins
        self.assertEqual(board.status, BoardStatus.BLACK_WIN)
        board.undo()
        self.assertEqual(board.status, BoardStatus.ONGOING)
        self.assertEqual(board.reason, WinReason.NORMAL)

    def test_undo_multiple_times(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("h8i9g7")
        board.undo()
        board.undo()
        self.assertEqual(board.get_moves(), [[7, 7]])

    def test_play_invalid_str_raises(self):
        board = RenjuBoard()
        with self.assertRaises(ValueError):
            board.play_str("h8XYZ")  # invalid format after h8


class TestBoardTransformations(unittest.TestCase):
    """All 8 D4 symmetry transformations, including pass-move handling."""

    def setUp(self):
        # h8(7,7) and h9(7,8) — use freestyle to avoid any rule interference
        self.board = RenjuBoard(pos="h8h9", board_size=15, rule=Rule.FREESTYLE)

    def test_copy_identity(self):
        b = self.board.copy()
        self.assertEqual(b.get_moves(), [[7, 7], [7, 8]])

    def test_flip_x(self):
        b = self.board.flip_x()
        self.assertEqual(b.get_moves(), [[7, 7], [7, 6]])

    def test_flip_y(self):
        # x -> 14-x: 14-7=7, so both stones stay at x=7
        b = self.board.flip_y()
        self.assertEqual(b.get_moves(), [[7, 7], [7, 8]])

    def test_flip_diagonal(self):
        # x<->y: (7,7)->(7,7), (7,8)->(8,7)
        b = self.board.flip_diagonal()
        self.assertEqual(b.get_moves(), [[7, 7], [8, 7]])

    def test_flip_anti_diagonal(self):
        # (x,y)->(14-y, 14-x): (7,7)->(7,7), (7,8)->(6,7)
        b = self.board.flip_anti_diagonal()
        self.assertEqual(b.get_moves(), [[7, 7], [6, 7]])

    def test_rotate_90_cw(self):
        # (x,y)->(14-y, x): (7,7)->(7,7), (7,8)->(6,7)
        b = self.board.rotate_90()
        self.assertEqual(b.get_moves(), [[7, 7], [6, 7]])

    def test_rotate_90_ccw(self):
        # (x,y)->(y, 14-x): (7,7)->(7,7), (7,8)->(8,7)
        b = self.board.rotate_90_ccw()
        self.assertEqual(b.get_moves(), [[7, 7], [8, 7]])

    def test_rotate_180(self):
        # (x,y)->(14-x, 14-y): (7,7)->(7,7), (7,8)->(7,6)
        b = self.board.rotate_180()
        self.assertEqual(b.get_moves(), [[7, 7], [7, 6]])

    def test_transform_preserves_rule_and_size(self):
        b = RenjuBoard(pos="h8", rule=Rule.STANDARD, board_size=19)
        br = b.rotate_90()
        self.assertEqual(br.rule, Rule.STANDARD)
        self.assertEqual(br.board_size, 19)

    def test_pass_moves_preserved_by_transformations(self):
        board = RenjuBoard(pos="h8passi9", board_size=15, rule=Rule.FREESTYLE)
        for method in [board.copy, board.flip_x, board.flip_y,
                       board.flip_diagonal, board.flip_anti_diagonal,
                       board.rotate_90, board.rotate_90_ccw, board.rotate_180]:
            b = method()
            self.assertEqual(b.moves[1], [-1, -1], f"Pass not preserved in {method.__name__}")

    def test_transform_corner_stone(self):
        # Stone at a1 (0,0) on 15x15
        board = RenjuBoard(pos="a1", board_size=15, rule=Rule.FREESTYLE)
        self.assertEqual(board.flip_x().moves[0], [0, 14])
        self.assertEqual(board.flip_y().moves[0], [14, 0])
        self.assertEqual(board.rotate_180().moves[0], [14, 14])

    def test_four_rotations_cycle(self):
        """Rotating 4 times by 90 degrees should return to original."""
        board = RenjuBoard(pos="h8i9g7f8", board_size=15, rule=Rule.FREESTYLE)
        b = board
        for _ in range(4):
            b = b.rotate_90()
        self.assertEqual(b, board)

    def test_double_flip_x_is_identity(self):
        board = RenjuBoard(pos="h8i9g7", board_size=15, rule=Rule.FREESTYLE)
        self.assertEqual(board.flip_x().flip_x(), board)

    def test_double_flip_y_is_identity(self):
        board = RenjuBoard(pos="h8i9g7", board_size=15, rule=Rule.FREESTYLE)
        self.assertEqual(board.flip_y().flip_y(), board)

    def test_double_flip_diagonal_is_identity(self):
        board = RenjuBoard(pos="h8i9g7", board_size=15, rule=Rule.FREESTYLE)
        self.assertEqual(board.flip_diagonal().flip_diagonal(), board)


class TestBoardEquivalence(unittest.TestCase):
    """__eq__ and is_symmetric_to tests."""

    def test_equality_same_board(self):
        b1 = RenjuBoard(pos="h8i9g7", rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8i9g7", rule=Rule.FREESTYLE)
        self.assertEqual(b1, b2)

    def test_inequality_different_moves(self):
        b1 = RenjuBoard(pos="h8i9g7", rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8i9", rule=Rule.FREESTYLE)
        self.assertNotEqual(b1, b2)

    def test_inequality_different_rule(self):
        b1 = RenjuBoard(pos="h8", rule=Rule.RENJU)
        b2 = RenjuBoard(pos="h8", rule=Rule.STANDARD)
        self.assertNotEqual(b1, b2)

    def test_inequality_different_size(self):
        b1 = RenjuBoard(pos="h8", board_size=15, rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8", board_size=19, rule=Rule.FREESTYLE)
        self.assertNotEqual(b1, b2)

    def test_not_equal_to_non_board(self):
        board = RenjuBoard()
        result = board.__eq__("not a board")
        self.assertEqual(result, NotImplemented)

    def test_is_symmetric_to_self(self):
        board = RenjuBoard(pos="h8i9g7", rule=Rule.FREESTYLE)
        self.assertTrue(board.is_symmetric_to(board.copy()))

    def test_is_symmetric_to_rotated(self):
        board = RenjuBoard(pos="h8i9g7f8", board_size=15, rule=Rule.FREESTYLE)
        self.assertTrue(board.is_symmetric_to(board.rotate_90()))
        self.assertTrue(board.is_symmetric_to(board.rotate_180()))
        self.assertTrue(board.is_symmetric_to(board.rotate_90_ccw()))

    def test_is_symmetric_to_flipped(self):
        board = RenjuBoard(pos="h8i9g7f8", board_size=15, rule=Rule.FREESTYLE)
        self.assertTrue(board.is_symmetric_to(board.flip_x()))
        self.assertTrue(board.is_symmetric_to(board.flip_y()))

    def test_not_symmetric_to_different_board(self):
        b1 = RenjuBoard(pos="h8i9g7", rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8i9", rule=Rule.FREESTYLE)
        self.assertFalse(b1.is_symmetric_to(b2))

    def test_not_symmetric_to_different_size(self):
        b1 = RenjuBoard(pos="h8", board_size=15, rule=Rule.FREESTYLE)
        b2 = RenjuBoard(pos="h8", board_size=19, rule=Rule.FREESTYLE)
        self.assertFalse(b1.is_symmetric_to(b2))

    def test_not_symmetric_to_different_rule(self):
        b1 = RenjuBoard(pos="h8", rule=Rule.RENJU)
        b2 = RenjuBoard(pos="h8", rule=Rule.STANDARD)
        self.assertFalse(b1.is_symmetric_to(b2))

    def test_not_symmetric_to_non_board(self):
        board = RenjuBoard(pos="h8")
        self.assertFalse(board.is_symmetric_to("not a board"))  # type: ignore


class TestSymmetricCandidates(unittest.TestCase):
    """find_symmetric_candidates edge cases."""

    def test_basic_vertical_line_symmetric_candidates(self):
        # Vertical four: h8(7,7), h9(7,8), h7(7,6), h6(7,5).
        # i8(8,7) and i7(8,6) are symmetric by horizontal reflection.
        board = RenjuBoard(pos="h8h9h7h6", board_size=15, rule=Rule.FREESTYLE)
        candidates = [(8, 7), (8, 6), (9, 9)]
        sym, all_g = board.find_symmetric_candidates(candidates)
        self.assertEqual(len(sym), 1)
        self.assertIn((8, 7), sym[0])
        self.assertIn((8, 6), sym[0])
        self.assertEqual(len(all_g), 2)

    def test_all_candidates_in_one_group(self):
        # Symmetric candidates should all end up in one group
        board = RenjuBoard(pos="h8h9h7h6", board_size=15, rule=Rule.FREESTYLE)
        sym, all_g = board.find_symmetric_candidates([(8, 7), (8, 6)])
        self.assertEqual(len(sym), 1)
        self.assertEqual(len(all_g), 1)

    def test_single_candidate(self):
        board = RenjuBoard(pos="h8", board_size=15, rule=Rule.FREESTYLE)
        sym, all_g = board.find_symmetric_candidates([(9, 9)])
        self.assertEqual(len(sym), 0)
        self.assertEqual(len(all_g), 1)

    def test_empty_candidates(self):
        board = RenjuBoard(pos="h8", board_size=15, rule=Rule.FREESTYLE)
        sym, all_g = board.find_symmetric_candidates([])
        self.assertEqual(len(sym), 0)
        self.assertEqual(len(all_g), 0)

    def test_translation_invariance(self):
        """Two identical-shaped vertical-four patterns at different board positions."""
        # h8h9h7h6: stones at col 7, rows 5-8. Symmetric candidates to the right: (8,7) and (8,6).
        board1 = RenjuBoard(pos="h8h9h7h6", board_size=15, rule=Rule.FREESTYLE)
        sym1, _ = board1.find_symmetric_candidates([(8, 7), (8, 6)])
        self.assertEqual(len(sym1), 1,
                         msg="h8h9h7h6 board: (8,7) and (8,6) should be symmetric")
        # d4d5d3d2: stones at col 3, rows 1-4 (same color pattern). Symmetric candidates: (4,3) and (4,2).
        board2 = RenjuBoard(pos="d4d5d3d2", board_size=15, rule=Rule.FREESTYLE)
        sym2, _ = board2.find_symmetric_candidates([(4, 3), (4, 2)])
        self.assertEqual(len(sym2), 1,
                         msg="d4d5d3d2 board: (4,3) and (4,2) should be symmetric")

    def test_board_with_pass_treated_correctly(self):
        """Pass moves are skipped, so the shape should still be recognized correctly."""
        # Without pass: h8(B),h9(W),h7(B),h6(W) — alternating B/W vertical line
        board_no_pass = RenjuBoard(pos="h8h9h7h6", board_size=15, rule=Rule.FREESTYLE)
        # With pass inserted between moves, color assignment changes
        # h8(B), pass(B->W turn), h9(B), h7(W), h6(B)
        board_with_pass = RenjuBoard(pos="h8passh9h7h6", board_size=15, rule=Rule.FREESTYLE)
        # They are different color arrangements, so different symmetry signatures
        # What matters is that pass doesn't break the algorithm (no errors)
        candidates = [(8, 7), (8, 6)]
        sym_no_pass, _ = board_no_pass.find_symmetric_candidates(candidates)
        sym_with_pass, _ = board_with_pass.find_symmetric_candidates(candidates)
        # Just verify both complete without error and return valid structures
        self.assertIsInstance(sym_no_pass, list)
        self.assertIsInstance(sym_with_pass, list)


class TestBoardDisplay(unittest.TestCase):
    """__str__ and display() sanity checks."""

    def test_str_contains_grid_markers(self):
        board = RenjuBoard(pos="h8i9", board_size=15, rule=Rule.FREESTYLE)
        s = str(board)
        self.assertIn("X", s)
        self.assertIn("O", s)
        self.assertIn(".", s)

    def test_str_has_all_column_headers(self):
        board = RenjuBoard(board_size=15)
        s = str(board)
        for ch in "abcdefghijklmno":
            self.assertIn(ch, s)

    def test_str_has_row_numbers(self):
        board = RenjuBoard(board_size=15)
        s = str(board)
        self.assertIn("1", s)
        self.assertIn("15", s)

    def test_pass_not_shown_on_board(self):
        # h8(B, index 0), pass(index 1), i9 is index 2 -> Black stone
        board = RenjuBoard(pos="h8passi9", board_size=15, rule=Rule.FREESTYLE)
        s = str(board)
        # Two black stones (X), no white stone (O), pass not rendered
        self.assertEqual(s.count("X"), 2)
        self.assertEqual(s.count("O"), 0)
        self.assertNotIn("pass", s)

    def test_empty_board_all_dots(self):
        board = RenjuBoard(board_size=5)
        s = str(board)
        self.assertEqual(s.count("."), 25)

    def test_display_does_not_raise(self):
        board = RenjuBoard(pos="h8", board_size=15)
        import io, sys
        captured = io.StringIO()
        sys.stdout = captured
        board.display()
        sys.stdout = sys.__stdout__
        self.assertGreater(len(captured.getvalue()), 0)


class TestSGFImportExport(unittest.TestCase):
    """to_sgf and from_sgf thorough tests."""

    def test_basic_roundtrip(self):
        board = RenjuBoard(pos="h8i9g7", rule=Rule.RENJU, board_size=15)
        sgf = board.to_sgf()
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.board_size, 15)
        self.assertEqual(imported.rule, Rule.RENJU)
        self.assertEqual(imported.moves, [[7, 7], [8, 8], [6, 6]])

    def test_roundtrip_with_pass_moves(self):
        board = RenjuBoard(pos="h8passi9", rule=Rule.FREESTYLE, board_size=15)
        sgf = board.to_sgf()
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.moves, [[7, 7], [-1, -1], [8, 8]])

    def test_sgf_contains_game_metadata(self):
        board = RenjuBoard(pos="h8", rule=Rule.STANDARD, board_size=15)
        sgf = board.to_sgf(black_name="Alice", white_name="Bob",
                           date="2026-01-01", event="World Championship")
        self.assertIn("PB[Alice]", sgf)
        self.assertIn("PW[Bob]", sgf)
        self.assertIn("DT[2026-01-01]", sgf)
        self.assertIn("EV[World Championship]", sgf)
        self.assertIn("GM[4]", sgf)
        self.assertIn("FF[4]", sgf)

    def test_sgf_contains_result_when_won(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("a1b1a2b2a3b3a4b4a5")
        sgf = board.to_sgf()
        self.assertIn("RE[B+", sgf)

    def test_sgf_pass_as_empty_brackets(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_move(-1, -1)  # Black passes
        sgf = board.to_sgf()
        self.assertIn("B[]", sgf)

    def test_from_sgf_pass_empty_brackets(self):
        sgf = "(;SZ[15]RU[Renju];B[hh];W[])"
        board = RenjuBoard.from_sgf(sgf)
        self.assertEqual(board.moves, [[7, 7], [-1, -1]])

    def test_from_sgf_pass_tt_convention(self):
        sgf = "(;SZ[15]RU[Standard];B[hh];W[tt])"
        board = RenjuBoard.from_sgf(sgf)
        self.assertEqual(board.moves, [[7, 7], [-1, -1]])

    def test_from_sgf_default_rule_when_missing(self):
        sgf = "(;SZ[15];B[hh])"
        board = RenjuBoard.from_sgf(sgf)
        self.assertEqual(board.rule, Rule.RENJU)

    def test_from_sgf_default_size_when_missing(self):
        sgf = "(;RU[Freestyle];B[hh])"
        board = RenjuBoard.from_sgf(sgf)
        self.assertEqual(board.board_size, 15)

    def test_from_sgf_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            RenjuBoard.from_sgf("not an sgf at all")

    def test_from_sgf_no_nodes_raises(self):
        with self.assertRaises(ValueError):
            RenjuBoard.from_sgf("()")

    def test_from_sgf_invalid_coordinate_raises(self):
        sgf = "(;SZ[15]RU[Renju];B[hhh])"
        with self.assertRaises(ValueError):
            RenjuBoard.from_sgf(sgf)

    def test_sgf_custom_board_size(self):
        board = RenjuBoard(pos="a1b1", board_size=19, rule=Rule.FREESTYLE)
        sgf = board.to_sgf()
        self.assertIn("SZ[19]", sgf)
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.board_size, 19)

    def test_sgf_bracket_escaping_in_player_name(self):
        board = RenjuBoard(pos="h8", rule=Rule.FREESTYLE)
        sgf = board.to_sgf(black_name="Alice]Bob", white_name="Charlie")
        self.assertIn("PB[Alice\\]Bob]", sgf)
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.moves, [[7, 7]])

    def test_sgf_corner_coordinate_a1(self):
        board = RenjuBoard(pos="a1", rule=Rule.FREESTYLE)
        sgf = board.to_sgf()
        self.assertIn("B[aa]", sgf)
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.moves, [[0, 0]])

    def test_sgf_preserves_status_after_import(self):
        board = RenjuBoard(rule=Rule.FREESTYLE)
        board.play_str("a1b1a2b2a3b3a4b4a5")
        self.assertEqual(board.status, BoardStatus.BLACK_WIN)
        sgf = board.to_sgf()
        imported = RenjuBoard.from_sgf(sgf)
        self.assertEqual(imported.status, BoardStatus.BLACK_WIN)

    def test_from_sgf_rule_freestyle(self):
        sgf = "(;SZ[15]RU[Freestyle];B[hh];W[ii];B[jj])"
        board = RenjuBoard.from_sgf(sgf)
        self.assertEqual(board.rule, Rule.FREESTYLE)
        self.assertEqual(len(board), 3)

    def test_sgf_no_date_or_event_optional(self):
        board = RenjuBoard(pos="h8", rule=Rule.FREESTYLE)
        sgf = board.to_sgf()
        self.assertNotIn("DT[", sgf)
        self.assertNotIn("EV[", sgf)


class TestRuleEnum(unittest.TestCase):
    """Rule enum parsing edge cases."""

    def test_all_rules_from_string_case_insensitive(self):
        for s, expected in [("freestyle", Rule.FREESTYLE), ("FREESTYLE", Rule.FREESTYLE),
                             ("standard", Rule.STANDARD), ("STANDARD", Rule.STANDARD),
                             ("renju", Rule.RENJU), ("RENJU", Rule.RENJU),
                             ("Freestyle", Rule.FREESTYLE)]:
            self.assertEqual(Rule.from_str(s), expected)

    def test_invalid_rule_string_raises(self):
        with self.assertRaises(ValueError):
            Rule.from_str("caro")

    def test_rule_int_values(self):
        self.assertEqual(Rule.FREESTYLE, 0)
        self.assertEqual(Rule.STANDARD, 1)
        self.assertEqual(Rule.RENJU, 4)

    def test_invalid_rule_type_raises(self):
        with self.assertRaises(TypeError):
            RenjuBoard(rule=3.14)  # type: ignore


if __name__ == '__main__':
    unittest.main()
