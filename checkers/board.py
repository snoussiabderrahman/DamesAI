import pygame
from .constants import BROWN, ROWS, CREAM, SQUARE_SIZE, COLS, BLACK
from .piece import Piece

class Board:
     
    def __init__(self):
        self.board = []
        self.cream_left = self.black_left = 12
        self.cream_kings = self.black_kings = 0
        self.create_board()
    
    def draw_squares(self, win):
        win.fill(BROWN)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, CREAM, (row*SQUARE_SIZE, col *SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def move(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        if (row == ROWS - 1 or row == 0) and piece.king == False:
            piece.make_king()
            if piece.color == BLACK:
                self.black_kings += 1
                self.black_left -= 1
            else:
                self.cream_kings += 1 
                self.cream_left -= 1

    def get_piece(self, row, col):
        return self.board[row][col]

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row +  1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, BLACK))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, CREAM))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)
    
    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def print_board(self):
        for row in range(ROWS):
            for col in range(COLS):
                print(self.board[row][col])

    def remove(self, pieces):
        for piece in pieces:
            if piece != 0:
                self.board[piece.row][piece.col] = 0
                if piece.king:
                    if piece.color == CREAM:
                        self.cream_kings -= 1
                    else:
                        self.black_kings -= 1
                else:
                    if piece.color == CREAM:
                        self.cream_left -= 1
                    else:
                        self.black_left -= 1

    def winner(self, color):
        if self.black_left == 0 and self.black_kings == 1 and self.cream_left == 0 and self.cream_kings == 1:
            return "Equal"
        
        pieces = self.get_all_pieces(color)
        for piece in pieces:
            moves = self.get_valid_moves(piece)
            if moves:
                return None
        if color == CREAM:
            return "PLAYER black WINS!"
        else:
            return "Player cream WINS!"
        
 
    '''
    def get_valid_moves(self, piece):
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if not piece.king:
            if piece.color == CREAM:
                moves.update(self.traverse_left(row -1, max(row-3, -1), -1, piece.color, left))
                moves.update(self.traverse_right(row -1, max(row-3, -1), -1, piece.color, right))
            if piece.color == BLACK :
                moves.update(self.traverse_left(row +1, min(row+3, ROWS), 1, piece.color, left))
                moves.update(self.traverse_right(row +1, min(row+3, ROWS), 1, piece.color, right))
        else:
            moves.update(self.traverse_left_king(row -1, max(row-3, -1), -1, piece.color, left, [piece.row, piece.col]))
            moves.update(self.traverse_right_king(row -1, max(row-3, -1), -1, piece.color, right, [piece.row, piece.col]))
            moves.update(self.traverse_left_king(row +1, min(row+3, ROWS), 1, piece.color, left, [piece.row, piece.col]))
            moves.update(self.traverse_right_king(row +1, min(row+3, ROWS), 1, piece.color, right, [piece.row, piece.col]))
        return moves
    '''
    def get_valid_moves(self, piece):
        moves = {}
        if piece.king:
            # For kings, we get all possible valid moves, both jumps and simple moves.
            # The game logic will later filter to enforce mandatory jumps.
            moves.update(self._find_king_moves(piece.row, piece.col, piece.color))
        else:
            # The logic for men remains the same as it was.
            left = piece.col - 1
            right = piece.col + 1
            row = piece.row
            if piece.color == CREAM:
                moves.update(self.traverse_left(row - 1, max(row-3, -1), -1, piece.color, left))
                moves.update(self.traverse_right(row - 1, max(row-3, -1), -1, piece.color, right))
            if piece.color == BLACK:
                moves.update(self.traverse_left(row + 1, min(row+3, ROWS), 1, piece.color, left))
                moves.update(self.traverse_right(row + 1, min(row+3, ROWS), 1, piece.color, right))
        
        return moves

    def _find_king_moves(self, row, col, color, skipped=[]):
        moves = {}
        # Iterate through the 4 diagonal directions (up-left, up-right, down-left, down-right)
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            
            path_moves = {}
            jump_found_on_path = False

            # Scan along one diagonal path
            for i in range(1, ROWS):
                r, c = row + i * dr, col + i * dc

                # If we go off the board, stop scanning this path
                if not (0 <= r < ROWS and 0 <= c < COLS):
                    break

                current_piece = self.board[r][c]

                if current_piece == 0: # Empty square
                    if jump_found_on_path:
                        # This is a valid landing spot after a jump
                        path_moves[(r,c)] = jump_found_on_path
                    elif not skipped:
                        # This is a simple (non-capture) move
                        moves[(r,c)] = []
                    continue # Continue scanning along the path

                # If we find a piece of the same color, the path is blocked
                elif current_piece.color == color:
                    break

                # If we find an opponent's piece
                else:
                    # If we've already jumped a piece on this path, we can't jump another (two in a row)
                    if jump_found_on_path:
                        break
                    
                    # Check if this piece has already been jumped in the current sequence
                    if current_piece in skipped:
                        break
                    
                    # This is the piece we can potentially jump over
                    jump_found_on_path = [current_piece]

            # After scanning a full diagonal, if we found jumps, we need to explore multi-jumps
            if path_moves:
                for (end_r, end_c), jumped_piece in path_moves.items():
                    # Add the move to the main moves dictionary
                    new_skipped = skipped + jumped_piece
                    moves[(end_r, end_c)] = new_skipped

                    # Recursively check for more jumps from this landing spot
                    # We pass the new list of skipped pieces to the recursive call
                    more_moves = self._find_king_moves(end_r, end_c, color, new_skipped)
                    
                    # We only care about further JUMPS, not simple moves from the new spot
                    for move, more_skipped in more_moves.items():
                        if more_skipped: # If it's a jump
                            moves[move] = more_skipped
        return moves


    def traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, left)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, -1)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self.traverse_left(r+step, row, step, color, left-1,new_skipped))
                    moves.update(self.traverse_right(r+step, row, step, color, left+1,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1
        
        return moves

    def traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r,right)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, right)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, -1)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self.traverse_left(r+step, row, step, color, right-1,new_skipped))
                    moves.update(self.traverse_right(r+step, row, step, color, right+1,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1
        
        return moves
    
    ##########################################################
    '''
    def traverse_left_king(self, start, stop, step, color, left, piece ,skipped=[]):
        moves = {}
        last = []
        if piece[0] == start and piece[1] == left:
            return moves

        for r in range(start, stop, step):
            if left < 0:
                break
            
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, left)] = last
                
                if last:
                    row_max = max(r-3, -1) 
                    row_min = min(r+3, ROWS) 

                    piece = [r-step, left+1]
                    moves.update(self.traverse_left_king(r+step, row_max if step==-1 else row_min, step, color, left-1, piece,new_skipped))
                    moves.update(self.traverse_right_king(r+step, row_max if step==-1 else row_min, step, color, left+1, piece,new_skipped))
                    moves.update(self.traverse_left_king(r-step, row_max if step==1 else row_min, -step, color, left-1, piece,new_skipped))
                    moves.update(self.traverse_right_king(r-step, row_max if step==1 else row_min, -step, color, left+1, piece,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1
        
        return moves
    def traverse_right_king(self, start, stop, step, color, right, piece, skipped=[]):
        moves = {}
        last = []
        if piece[0] == start and piece[1] == right:
            return moves
        
        for r in range(start, stop, step):
            if right >= COLS:
                break
            
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r,right)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, right)] = last
                
                if last:
                    row_max = max(r-3, -1)
                    row_min = min(r+3, ROWS)

                    piece = [r-step, right-1]
                    moves.update(self.traverse_left_king(r+step, row_max if step==-1 else row_min, step, color, right-1, piece,new_skipped))
                    moves.update(self.traverse_right_king(r+step, row_max if step==-1 else row_min, step, color, right+1, piece,new_skipped))
                    moves.update(self.traverse_left_king(r-step, row_max if step==1 else row_min, -step, color, right-1, piece,new_skipped))
                    moves.update(self.traverse_right_king(r-step, row_max if step==1 else row_min, -step, color, right+1, piece,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1
        
        return moves
    #------------------#
    '''
    def evaluate(self, color):
        if color == BLACK:
            return self.black_left - self.cream_left +  (self.black_kings - self.cream_kings)/12
        else:
            return self.cream_left - self.black_left +  (self.cream_kings - self.black_kings)/12

    def get_all_pieces(self, color):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def get_board(self):
        return self.board

        
    

    
    