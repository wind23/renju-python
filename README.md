# Renju Library (五子棋/连珠棋盘库)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)

[English](#english) | [中文](#中文)

---

## English

A simple, lightweight Python library for representing, managing, and visualizing a Renju / Gomoku (五子棋) game board, verifying game state rules, performing symmetry transformations, and detecting symmetric candidate moves.

### Features
* **Rules & Forbidden Moves (Renju, Standard, Freestyle)**: Full referee rules logic integrated. Automatically checks for win conditions and Black forbidden moves (Double-three, Double-four, Overline) according to rule sets.
* **Win Reason Reporting**: Returns both the `BoardStatus` and the specific `WinReason` (e.g. five-in-a-row, double-three forbid) after every move.
* **Candidate Symmetry Grouping**: Evaluates whether any candidate coordinates, when added to the existing board layout, result in symmetric layouts. The algorithm is translation-invariant (ignores distance to board boundaries), rotation-invariant, and reflection-invariant. Essential for validating five-hand N-point plays (五手N打).
* **Pass Move Support**: Supports passing a turn (skipping placement) represented internally as coordinate `[-1, -1]` and string format as `"pass"`. Consecutive passes by both players results in a draw.
* **Bespoke Board Coordinates**: Easily convert between 0-based integer coordinates `(x, y)` and standard Excel-style string coordinates (e.g. `(7, 7)` $\leftrightarrow$ `"h8"`).
* **Flexible Parser**: Parse move sequences from clean strings (e.g., `"h8i9g7"`, `"h8passi9"`) or separator-formatted sequences as well as coordinate lists.
* **Interactive Play & Undo**: Dynamically play moves with `play_move` or `play_str`, check the current turn player, and undo moves (which recalculates the rules state).
* **Symmetry Transformations**: Dihedral group of 8 square board transformations (`copy`, `flip_x`, `flip_y`, `flip_diagonal`, `flip_anti_diagonal`, `rotate_90`, `rotate_90_ccw`, `rotate_180`) returning new transformed `RenjuBoard` instances.
* **Equivalence & Isomorphism Check**: Check exact equality of two boards (`==`) or whether two boards are isomorphic/equivalent under any of the 8 symmetries (`is_symmetric_to`).
* **Terminal Board Visualization**: High fidelity board printing representation (`__str__` / `display()`) showing current black (`X`) and white (`O`) positions with custom grids.
* **SGF Import & Export**: Serializes and parses game logs to/from standard SGF (Smart Game Format, `GM[4]`), correctly preserving player names, dates, results, rules, and pass moves.

### Installation

```bash
pip install renju
```

### Quick Start

```python
from renju import RenjuBoard, Rule, BoardStatus, WinReason

# 1. Initialize board (size 15x15) with Renju rule set
board = RenjuBoard(board_size=15, rule=Rule.RENJU)

# 2. Dynamic plays & rules checking (returns status, reason)
status, reason = board.play_move(7, 7) # play h8
print(status)  # Output: BoardStatus.ONGOING

# 3. Find symmetric candidate moves (useful for N-point plays validation)
# Existing configuration: vertical line (h8, h9, h7, h6)
board_line = RenjuBoard(pos="h8h9h7h6")
# Candidates: i8(8,7) and i7(8,6)
candidates = [(8, 7), (8, 6), (9, 9)]
symmetric_groups, all_groups = board_line.find_symmetric_candidates(candidates)

print(symmetric_groups) # Output: [[(8, 7), (8, 6)]] -> i8 and i7 are symmetric configurations!
print(all_groups)       # Output: [[(8, 7), (8, 6)], [(9, 9)]]

# 4. Pass support
status, reason = board.play_move(-1, -1) # B passes

# 5. Undo restores board and recalculates game state
board.undo()

# 6. Display the board in terminal
board.display()

# 7. SGF Export & Import
sgf_string = board.to_sgf(black_name="Alice", white_name="Bob", date="2026-06-07")
imported_board = RenjuBoard.from_sgf(sgf_string)
```

---

## 中文

一个轻量级的 Python 库，用于表示、管理和可视化连珠/五子棋（Renju / Gomoku）的棋盘状态和落子序列，并支持游戏规则校验、对称变换及候选等价点查找。

### 主要功能
* **规则与禁手校验（连珠、标准、自由规则）**：内置裁判规则引擎，自动判定胜负以及黑棋禁手（三三禁手、四四禁手、长连禁手）。五连与禁手同时出现时，优先判定五连获胜。
* **返回获胜原因**：每次落子后都会返回包含当前棋局状态 `BoardStatus` 和具体原因 `WinReason` 的元组。
* **打点对称等价性判定（平移、旋转、翻转无关）**：输入多个坐标，判断这些点与棋盘已有棋局组合后是否有部分对称（同构）。算法消除了棋形到盘端距离的差异（平移无关），且支持 8 个角度的翻转/旋转检测。此算法特别适用于五手N打（五手多打）的非法对称打点校验。
* **Pass（过牌/不落子）支持**：支持略过一手棋。在坐标序列中以 `[-1, -1]` 表示，字符串表示为 `"pass"`。若双方连续过牌，判定为和棋。
* **优雅的坐标转换**：轻松在从 0 开始的整型坐标 `(x, y)` 与标准的字母数字棋盘坐标之间进行双向转换。
* **灵活的落子序列解析**：支持直接通过连贯的字符串（如 `"h8i9g7"`、`"h8passi9"`）、带分隔符的文本或坐标对列表来初始化棋盘。
* **交互式对弈与悔棋**：提供 `play_move`、`play_str` 与 `undo` 方法。悔棋时会自动重新计算并恢复到历史棋局对应的正确规则状态。
* **对称变换**：内置 8 种棋盘对称与旋转操作，且能正确处理过牌步。
* **等价性与同构性检查**：支持直接通过 `==` 检查两棋盘是否完全一致，或使用 `is_symmetric_to` 检查两棋盘在旋转/镜像变换后是否等价（同构）。
* **棋盘可视化**：能够在终端直接绘制出直观的棋盘（黑棋为 `X`，白棋为 `O`，空位为 `.`，自动跳过过牌步）。
* **SGF 棋谱导入与导出**：支持标准 SGF（Smart Game Format）棋谱格式的读取与保存，支持记录对局信息（如棋手名字、对局日期、胜负结果及具体原因等），完美支持过牌（Pass）步骤的解析与还原。

### 安装方式

```bash
pip install renju
```

### 快速上手

```python
from renju import RenjuBoard, Rule, BoardStatus, WinReason

# 1. 初始化一个 15x15 的连珠规则棋盘
board = RenjuBoard(board_size=15, rule=Rule.RENJU)

# 2. 动态落子与规则状态获取
status, reason = board.play_move(7, 7) # 在 h8 落子
print(status)  # 输出: BoardStatus.ONGOING

# 3. 查找对称打点（五手N打校验）
# 现有棋局：垂直的一条四连线：h8(7,7), h9(7,8), h7(7,6), h6(7,5)
board_line = RenjuBoard(pos="h8h9h7h6")
# 给定打点坐标：i8(8,7)、i7(8,6) 和 j10(9,9)
candidates = [(8, 7), (8, 6), (9, 9)]
symmetric_groups, all_groups = board_line.find_symmetric_candidates(candidates)

print(symmetric_groups) # 输出: [[(8, 7), (8, 6)]] -> i8 和 i7 生成的棋形对称！
print(all_groups)       # 输出: [[(8, 7), (8, 6)], [(9, 9)]]

# 4. Pass 过牌支持
status, reason = board.play_move(-1, -1) # 黑棋过牌

# 5. 悔棋将自动重新计算并恢复棋局状态
board.undo()

# 6. 在控制台打印可视化棋盘
board.display()

# 7. SGF 棋谱导入与导出
sgf_string = board.to_sgf(black_name="Alice", white_name="Bob", date="2026-06-07")
imported_board = RenjuBoard.from_sgf(sgf_string)
```
