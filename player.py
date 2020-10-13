"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, \
    ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, \
    SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    ans = []
    num_player = num_human + num_random + len(smart_players)
    goals = generate_goals(num_player)
    for i in range(num_human):
        ans.append(HumanPlayer(i, goals[i]))
    for i in range(num_human, num_human + num_random):
        ans.append(RandomPlayer(i, goals[i]))
    for i in range(num_random + num_human,
                   num_human + num_random + len(
                       smart_players)):
        ans.append(SmartPlayer(i, goals[i],
                               smart_players[i -
                                             num_random -
                                             num_human]))
    return ans


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    if block.position[0] <= location[0] < \
            block.position[0] + block.size and \
            block.position[1] <= location[1] < \
            block.position[1] + block.size:
        if len(block.children) == 0:
            return block
        if level == block.level:
            return block
        for child in block.children:
            temp = _get_block(child, location, level)
            if temp is not None:
                return temp
        return None
    else:
        return None
    # if len(block.children) == 0:
    #     return block
    # if level == 0:
    #     return block
    # else:
    #     for child in block.children:
    #         if _get_block(child, location, level - 1) is not None:
    #             return child
    #     return None


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    if block.max_depth - block.level == 0:
        return [[block.colour]]

    ans = []
    if len(block.children) == 0:
        for i in range(
                2 ** (block.max_depth - block.level)):
            ans.append([])
            for _ in range(
                    2 ** (block.max_depth - block.level)):
                ans[i].append(block.colour)
    else:
        flatten_child_ur = _flatten(block.children[0])
        flatten_child_ul = _flatten(block.children[1])
        flatten_child_ll = _flatten(block.children[2])
        flatten_child_lr = _flatten(block.children[3])
        for i in range(len(flatten_child_ul)):
            ans.append(
                flatten_child_ul[i] + flatten_child_ll[i])
        for i in range(len(flatten_child_ur)):
            ans.append(
                flatten_child_ur[i] + flatten_child_lr[i])
    return ans


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError

    def _player_helper(self, lst_copy: List[Block]) \
            -> Tuple[Tuple[str, Optional[int]], int]:
        """return a valid random action."""
        moves_possible = [ROTATE_CLOCKWISE,
                          ROTATE_COUNTER_CLOCKWISE,
                          SWAP_HORIZONTAL,
                          SWAP_VERTICAL, SMASH, PAINT, COMBINE]
        pot_action, pot_block_index = PASS, 0
        move_successful = False
        while not move_successful:
            pot_block_index = random.randint(0, len(lst_copy) - 1)
            pot_action = random.choice(moves_possible)
            if pot_action in [ROTATE_CLOCKWISE,
                              ROTATE_COUNTER_CLOCKWISE]:
                move_successful = lst_copy[
                    pot_block_index].rotate(pot_action[1])
            elif pot_action in [SWAP_HORIZONTAL, SWAP_VERTICAL]:
                move_successful = lst_copy[
                    pot_block_index].swap(pot_action[1])
            elif pot_action == SMASH:
                move_successful = lst_copy[
                    pot_block_index].smash()
            elif pot_action == PAINT:
                move_successful = lst_copy[
                    pot_block_index].paint(self.goal.colour)
            elif pot_action == COMBINE:
                move_successful = lst_copy[
                    pot_block_index].combine()
        return pot_action, pot_block_index


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    """Return a move that is made on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on. """
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player."""
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A Random Player. """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.

    # === Public Attributes ===
    # id:
    #     This player's number.
    # goal:
    #     This player's assigned goal for the game.
    id: int
    goal: Goal
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

       If no block is selected by the player, return None.
       """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        # to randomly choose a block we first create a list of all the blocks
        copy_board = board.create_copy()
        lst_copy = _board_all_blocks(copy_board)
        lst_original = _board_all_blocks(board)
        pot_action, pot_block_index = self._player_helper(lst_copy)
        # moves_possible = [ROTATE_CLOCKWISE,
        #                   ROTATE_COUNTER_CLOCKWISE,
        #                   SWAP_HORIZONTAL,
        #                   SWAP_VERTICAL, SMASH, PAINT, COMBINE]
        # pot_action, pot_block_index = PASS, 0
        # move_successful = False
        # while not move_successful:
        #     pot_block_index = random.randint(
        #     0, len(lst_copy))
        #     pot_action = random.choice(moves_possible)
        #     if pot_action in [ROTATE_CLOCKWISE,
        #     ROTATE_COUNTER_CLOCKWISE]:
        #         move_successful = lst_copy[
        #         pot_block_index].rotate(pot_action[1])
        #     elif pot_action in [SWAP_HORIZONTAL,
        #     SWAP_VERTICAL]:
        #         move_successful = lst_copy[
        #         pot_block_index].swap(pot_action[1])
        #     elif pot_action == SMASH:
        #         move_successful = lst_copy[
        #         pot_block_index].smash()
        #     elif pot_action == PAINT:
        #         move_successful = lst_copy[
        #         pot_block_index].paint(self.goal.colour)
        #     elif pot_action == COMBINE:
        #         move_successful = lst_copy[
        #         pot_block_index].combine()
        ans_move = _create_move(pot_action, lst_original[pot_block_index])
        self._proceed = False  # Must set to False before returning!
        return ans_move


class SmartPlayer(Player):
    """A Smart Player """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    # _difficulty:
    #   An integer that represent the difficulty level met by the player.
    # === Public Attributes ===
    # id:
    #     This player's number.
    # goal:
    #     This player's assigned goal for the game.
    id: int
    goal: Goal
    _proceed: bool
    _difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        Player.__init__(self, player_id, goal)
        self._difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    # def _any_possible_move(self, board: Block) -> bool:
    #     """Return True if there is a possible move on the board."""
    #     lst_original = _board_all_blocks(board)
    #     for i in range(len(lst_original)):
    #         moves_possible = [ROTATE_CLOCKWISE,
    #                           ROTATE_COUNTER_CLOCKWISE,
    #                           SWAP_HORIZONTAL,
    #                           SWAP_VERTICAL, SMASH, PAINT, COMBINE]
    #         move_successful = False
    #         for move_ in moves_possible:
    #             copy_board = board.create_copy()
    #             lst_copy = _board_all_blocks(copy_board)
    #             if move_ in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE]:
    #                 move_successful = lst_copy[i].rotate(move_[1])
    #             elif move_ in [SWAP_HORIZONTAL, SWAP_VERTICAL]:
    #                 move_successful = lst_copy[i].swap(move_[1])
    #             elif move_ == SMASH:
    #                 move_successful = lst_copy[i].smash()
    #             elif move_ == PAINT:
    #                 move_successful = lst_copy[i].paint(self.goal.colour)
    #             elif move_ == COMBINE:
    #                 move_successful = lst_copy[i].combine()
    #             if move_successful:
    #                 return True
    #     return False

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        # to randomly choose a block we first create a list of all the blocks
        potential_moves = []
        lst_original = _board_all_blocks(board)
        # if not self._any_possible_move(board):
        #     return _create_move(PASS, board)
        for _ in range(self._difficulty):
            copy_board = board.create_copy()
            lst_copy = _board_all_blocks(copy_board)
            temp_action, temp_block_index = \
                self._player_helper(lst_copy)
            temp_score = self.goal.score(copy_board)
            potential_moves.append(
                (temp_action, temp_score, temp_block_index))
        max_score = self.goal.score(board)
        action = PASS
        block_index = 0
        for tup in potential_moves:
            if tup[1] > max_score:
                max_score = tup[1]
                action = tup[0]
                block_index = tup[-1]
        ans_move = _create_move(
            action, lst_original[block_index])
        self._proceed = False  # Must set to False before returning!
        return ans_move


def _board_all_blocks(board: Block) -> List[Block]:
    """return all the leaves in board"""
    if len(board.children) == 0:
        return [board]
    else:
        ans = [board]
        for child in board.children:
            ans.extend(_board_all_blocks(child))
        return ans


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
