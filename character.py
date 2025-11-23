import os
import arcade
from constants import PLAYER_SPEED, TILE_SIZE


def autoscale(img_path, target_size):
    """依據圖片原始大小，自動縮放到 tile 尺寸。"""
    tex = arcade.load_texture(img_path)
    scale = target_size / max(tex.width, tex.height)
    return scale


class Player(arcade.Sprite):
    def __init__(self):
        base = os.path.dirname(__file__)
        img = os.path.join(base, "assets", "pacman.png")

        scale = autoscale(img, TILE_SIZE)
        super().__init__(img, scale)

        self.change_x = 0
        self.change_y = 0
        self.next_change_x = 0
        self.next_change_y = 0
        
        # Start position at grid (1, 1) - top left walkable area
        # Y is inverted: row 1 in the array = (height - 1 - 1) in pixels
        self.center_x = 1 * TILE_SIZE + TILE_SIZE / 2
        self.center_y = (21 - 1 - 1) * TILE_SIZE + TILE_SIZE / 2
        self.speed = PLAYER_SPEED

    def update_movement(self, walls):
        # 1. Try to apply the queued turn if we are close to the center of a tile
        if self.next_change_x != 0 or self.next_change_y != 0:
            # Calculate distance to center of current tile
            pixel_x = self.center_x
            pixel_y = self.center_y
            
            # Find the center of the grid tile we are currently "in"
            # (using integer division to find grid col/row, then back to pixels)
            grid_x = int(pixel_x // TILE_SIZE) * TILE_SIZE + TILE_SIZE / 2
            grid_y = int(pixel_y // TILE_SIZE) * TILE_SIZE + TILE_SIZE / 2
            
            dist = ((pixel_x - grid_x) ** 2 + (pixel_y - grid_y) ** 2) ** 0.5
            
            # If we are currently not moving, immediately apply the next direction
            if self.change_x == 0 and self.change_y == 0:
                # Check if this direction is valid
                self.center_x += self.next_change_x * TILE_SIZE
                self.center_y += self.next_change_y * TILE_SIZE
                
                if not arcade.check_for_collision_with_list(self, walls):
                    # Valid move, reset position and set direction
                    self.center_x -= self.next_change_x * TILE_SIZE
                    self.center_y -= self.next_change_y * TILE_SIZE
                    self.change_x = self.next_change_x
                    self.change_y = self.next_change_y
                    self.next_change_x = 0
                    self.next_change_y = 0
                else:
                    # Blocked, just reset position
                    self.center_x -= self.next_change_x * TILE_SIZE
                    self.center_y -= self.next_change_y * TILE_SIZE

            # If we are close enough to the center, try to turn
            elif dist < self.speed:
                # Check if the new direction is blocked
                self.center_x = grid_x
                self.center_y = grid_y
                
                original_x = self.change_x
                original_y = self.change_y
                
                self.change_x = self.next_change_x
                self.change_y = self.next_change_y
                
                # Temporarily move to check collision
                self.center_x += self.change_x * TILE_SIZE
                self.center_y += self.change_y * TILE_SIZE
                
                if arcade.check_for_collision_with_list(self, walls):
                    # Blocked, revert direction
                    self.change_x = original_x
                    self.change_y = original_y
                else:
                    # Success, clear queued turn
                    self.next_change_x = 0
                    self.next_change_y = 0
                
                # Reset position for actual movement step
                self.center_x = grid_x
                self.center_y = grid_y

        # 2. Move in current direction
        self.center_x += self.change_x * self.speed
        self.center_y += self.change_y * self.speed

        # 3. Check for wall collision in current direction
        if arcade.check_for_collision_with_list(self, walls):
            # Hit a wall, stop and snap to previous valid position (center of tile)
            self.center_x -= self.change_x * self.speed
            self.center_y -= self.change_y * self.speed
            
            # Optional: Snap to exact center to look clean
            grid_x = int(self.center_x // TILE_SIZE) * TILE_SIZE + TILE_SIZE / 2
            grid_y = int(self.center_y // TILE_SIZE) * TILE_SIZE + TILE_SIZE / 2
            self.center_x = grid_x
            self.center_y = grid_y
            
            # Stop moving
            # self.change_x = 0
            # self.change_y = 0
            # Note: In Pacman, you usually keep "pushing" against the wall until you turn, 
            # but setting speed to 0 is also fine. Let's keep pushing but not move.
