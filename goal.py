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
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import math
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    ans = []
    options = [PerimeterGoal, BlobGoal]
    goal_type = random.choice(options)
    colours_ = random.sample(COLOUR_LIST, num_goals)
    if goal_type == PerimeterGoal:
        for colour in colours_:
            ans.append(PerimeterGoal(colour))
    else:
        for colour in colours_:
            ans.append(BlobGoal(colour))
    return ans


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
        for i in range(int(
                math.pow(2, (block.max_depth - block.level)))):
            ans.append([])
            for _ in range(int(
                    math.pow(2, (block.max_depth - block.level)))):
                ans[i].append(block.colour)
    else:
        flatten_child_ur = _flatten(block.children[0])
        flatten_child_ul = _flatten(block.children[1])
        flatten_child_ll = _flatten(block.children[2])
        flatten_child_lr = _flatten(block.children[3])
        for i in range(len(flatten_child_ul)):
            ans.append(flatten_child_ul[i]+flatten_child_ll[i])
        for i in range(len(flatten_child_ur)):
            ans.append(flatten_child_ur[i] + flatten_child_lr[i])
    return ans


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        # accumulator
        score = 0
        # first flatten the block
        flatten_block = _flatten(board)
        # see how many units on the perimeters are of colour c
        # corners count twice
        target_colour = self.colour
        for c in flatten_block[0]:
            if c == target_colour:
                score += 1
        for c in flatten_block[-1]:
            if c == target_colour:
                score += 1
        for lst in flatten_block:
            if lst[0] == target_colour:
                score += 1
            if lst[-1] == target_colour:
                score += 1
        return score

    def description(self) -> str:
        c = colour_name(self.colour)
        s = "Put the most possible units of a given" \
            " colour, {}.".format(c) +\
            "on the outer perimeter of the board."
        return s


class BlobGoal(Goal):
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        # create a flatten board
        f_board = _flatten(board)
        # create a visited
        size_of_board = len(f_board)
        visited = []
        for i in range(size_of_board):
            visited.append([])
            for j in range(size_of_board):
                visited[i].append(-1)
        # find the max
        max_blob = 0
        for i in range(size_of_board):
            for j in range(size_of_board):
                temp_count = self._undiscovered_blob_size(
                    (i, j), f_board, visited)
                if temp_count >= max_blob:
                    max_blob = temp_count
        return max_blob

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        # If <pos> is out of bounds for <board>, return 0.
        if pos[0] >= len(board) or pos[1] >= len(board) \
                or pos[0] < 0 or pos[1] < 0:
            return 0
        if board[pos[0]][pos[1]] != self.colour:
            visited[pos[0]][pos[1]] = 0
            return 0
        if visited[pos[0]][pos[1]] != -1:
            return 0
        else:
            ans = 1
            visited[pos[0]][pos[1]] = 1
            ans = ans + self._undiscovered_blob_size(
                (pos[0] + 1, pos[1]), board, visited)
            ans = ans + self._undiscovered_blob_size(
                (pos[0] - 1, pos[1]), board, visited)
            ans = ans + self._undiscovered_blob_size(
                (pos[0], pos[1] + 1), board, visited)
            ans = ans + self._undiscovered_blob_size(
                (pos[0], pos[1] - 1), board, visited)
        return ans

    def description(self) -> str:
        c = colour_name(self.colour)
        s = 'Aim for the largest blob of a given colour, {}.'.format(c)
        return s


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
