import arcade
from constants import TILE_SIZE


class Pellet(arcade.Sprite):
    def __init__(self, x, y):
        # Create a simple white circle for pellet
        super().__init__()
        
        # Use a simple white circle texture
        self.texture = arcade.make_soft_circle_texture(8, arcade.color.WHITE)
        
        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2


class PowerPellet(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Large bright yellow circle for power pellet
        self.texture = arcade.make_soft_circle_texture(16, arcade.color.YELLOW)
        
        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2
        
        # Animation properties
        self.pulse_timer = 0
        self.base_scale = 1.0
    
    def update(self, delta_time=1/60):
        """Make the power pellet pulse/blink"""
        self.pulse_timer += 0.1
        # Pulse between 0.8 and 1.2 scale
        self.scale = self.base_scale + 0.2 * abs(((self.pulse_timer % 2.0) - 1.0))
