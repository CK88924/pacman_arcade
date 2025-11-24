import arcade
import os
import random
from constants import *
from map_generator import generate_map
from character import Player, autoscale
from ghost_ai import Ghost
from item import Pellet, PowerPellet


class PacManGame(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Arcade Pac-Man")
        arcade.set_background_color(COLOR_BG)

        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.pellets = arcade.SpriteList()
        self.power_pellets = arcade.SpriteList()
        self.ghosts = arcade.SpriteList()
        self.player_list = arcade.SpriteList()

        self.map_data = generate_map()
        
        self.player = Player()
        self.player_list.append(self.player)
        
        self.load_map()
        
        self.reset_game()
        
        # Create Text objects for better performance
        self.score_text = arcade.Text("Score: 0", 10, 10, arcade.color.WHITE, 14)
        self.game_over_text = arcade.Text("GAME OVER", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.RED, 30, anchor_x="center")
        self.victory_text = arcade.Text("VICTORY!", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.GREEN, 30, anchor_x="center")


    def load_map(self):
        base = os.path.dirname(__file__)
        wall_img = os.path.join(base, "assets", "wall.png")
        wall_scale = autoscale(wall_img, TILE_SIZE)
        
        empty_positions = []

        for r, row in enumerate(self.map_data):
            for c, tile in enumerate(row):
                x = c * TILE_SIZE
                y = (len(self.map_data) - r - 1) * TILE_SIZE

                if tile == 1:  # Wall
                    wall = arcade.Sprite(wall_img, wall_scale)
                    wall.center_x = x + TILE_SIZE / 2
                    wall.center_y = y + TILE_SIZE / 2
                    self.walls.append(wall)

                elif tile == 2:  # Regular pellet
                    pellet = Pellet(x, y)
                    self.pellets.append(pellet)
                    empty_positions.append((x, y))
                    
                elif tile == 3:  # Power pellet
                    power = PowerPellet(x, y)
                    self.power_pellets.append(power)
                    empty_positions.append((x, y))
                
                elif tile == 0:  # Empty path
                    empty_positions.append((x, y))

        # Spawn 4 ghosts at different positions
        colors = ["red", "blue", "pink", "orange"]
        
        walkable_positions = set(empty_positions)
        
        valid_spawn_positions = []
        for x, y in empty_positions:
            has_exit = False
            for dx, dy in [(TILE_SIZE, 0), (-TILE_SIZE, 0), (0, TILE_SIZE), (0, -TILE_SIZE)]:
                neighbor = (x + dx, y + dy)
                if neighbor in walkable_positions:
                    has_exit = True
                    break
            if has_exit:
                valid_spawn_positions.append((x, y))
        
        print(f"Found {len(valid_spawn_positions)} valid spawn positions out of {len(empty_positions)}")
        
        if len(valid_spawn_positions) >= 4:
            random.shuffle(valid_spawn_positions)
            
            chosen_positions = []
            for pos in valid_spawn_positions:
                too_close = False
                for chosen in chosen_positions:
                    dist = abs(pos[0] - chosen[0]) + abs(pos[1] - chosen[1])
                    if dist < 5 * TILE_SIZE:
                        too_close = True
                        break
                if not too_close:
                    chosen_positions.append(pos)
                    if len(chosen_positions) >= 4:
                        break
            
            if len(chosen_positions) < 4:
                chosen_positions = valid_spawn_positions[:4]
            
            for i, color in enumerate(colors):
                x, y = chosen_positions[i]
                ghost = Ghost(x, y, color)
                ghost.validate_and_set_direction(self.walls)
                self.ghosts.append(ghost)
                print(f"Created {color} ghost at ({x}, {y}), moving ({ghost.change_x}, {ghost.change_y})")
    

    def reset_game(self):
        """重置遊戲狀態（不重新創建窗口）"""
        self.walls.clear()
        self.pellets.clear()
        self.power_pellets.clear()
        self.ghosts.clear()
        self.player_list.clear()
        
        self.map_data = generate_map()
        
        self.player = Player()
        self.player_list.append(self.player)
        
        self.load_map()
        
        self.score = 0
        self.game_state = "PLAYING"


    def on_key_press(self, key, modifiers):
        if self.game_state != "PLAYING":
            if key == arcade.key.R:
                self.reset_game()
                return
            return
            
        if key == arcade.key.UP:
            self.player.next_change_y = 1
            self.player.next_change_x = 0
        elif key == arcade.key.DOWN:
            self.player.next_change_y = -1
            self.player.next_change_x = 0
        elif key == arcade.key.LEFT:
            self.player.next_change_x = -1
            self.player.next_change_y = 0
        elif key == arcade.key.RIGHT:
            self.player.next_change_x = 1
            self.player.next_change_y = 0

    def on_key_release(self, key, modifiers):
        pass


    def on_update(self, delta_time):
        if self.game_state != "PLAYING":
            return

        self.power_pellets.update()
        
        self.player.update_movement(self.walls)
        
        for ghost in self.ghosts:
            ghost.update_ai(
                self.walls,
                self.player.center_x,
                self.player.center_y,
                self.player.change_x,
                self.player.change_y
            )
        
        # 碰撞判斷
        for ghost in self.ghosts:
            # eaten 狀態的鬼不參與碰撞
            if ghost.state == "eaten":
                continue

            if arcade.check_for_collision(self.player, ghost):
                if ghost.state == "frightened":
                    # 玩家吃鬼 → 不刪除，改呼叫 on_eaten()，Ghost 會自己回家重生
                    ghost.on_eaten()
                    self.score += 200
                else:
                    self.game_state = "GAME_OVER"

        # 普通豆子
        hit = arcade.check_for_collision_with_list(self.player, self.pellets)
        for pellet in hit:
            pellet.remove_from_sprite_lists()
            self.score += 10
        
        # Power Pellets
        power_hit = arcade.check_for_collision_with_list(self.player, self.power_pellets)
        for power in power_hit:
            power.remove_from_sprite_lists()
            self.score += 50
            for ghost in self.ghosts:
                ghost.set_frightened()
            
        if len(self.pellets) == 0 and len(self.power_pellets) == 0:
            self.game_state = "VICTORY"


    def on_draw(self):
        self.clear()
        self.walls.draw()
        self.pellets.draw()
        self.power_pellets.draw()
        self.ghosts.draw()
        self.player_list.draw()
        
        self.score_text.text = f"Score: {self.score}"
        self.score_text.draw()
        
        if self.game_state == "GAME_OVER":
            self.game_over_text.draw()
            restart_text = arcade.Text(
                "Press R to Restart",
                SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40,
                arcade.color.WHITE, 16, anchor_x="center"
            )
            restart_text.draw()
        elif self.game_state == "VICTORY":
            self.victory_text.draw()
            restart_text = arcade.Text(
                "Press R to Restart",
                SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40,
                arcade.color.WHITE, 16, anchor_x="center"
            )
            restart_text.draw()


if __name__ == "__main__":
    PacManGame()
    arcade.run()
