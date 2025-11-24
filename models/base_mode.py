from pathlib import Path
import arcade
import random

from constants import TILE_SIZE
from map_generator import generate_map
from character import Player, autoscale
from ghost_ai import Ghost
from item import Pellet, PowerPellet

# 專案根目錄：.../pacman_arcade
ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"


class BaseMode:
    def __init__(self):
        # 狀態
        self.score = 0
        self.finished = False
        self.result = None   # "GAME_OVER" / "VICTORY" / None

        # 物件
        self.walls = None
        self.pellets = None
        self.power_pellets = None
        self.ghosts = None
        self.player = None
        self.player_list = None

        # 鬼出生點（Endless 用）
        self.ghost_spawn_points = []

        self.setup_world()

    # ---------------- 世界建立 ----------------

    def setup_world(self):
        """重新產生整張地圖和所有物件"""
        self.map = generate_map()
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.pellets = arcade.SpriteList()
        self.power_pellets = arcade.SpriteList()
        self.ghosts = arcade.SpriteList()
        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)  # 修正：明確加入玩家
        self.load_map()

    def load_map(self):
        """從 self.map 建立牆、豆子、鬼 & 玩家出生點"""
        wall_img = ASSET_DIR / "wall.png"
        wall_scale = autoscale(str(wall_img), TILE_SIZE)

        empty = []  # 所有可走路座標（給鬼 & 玩家用）
        height = len(self.map)

        for r, row in enumerate(self.map):
            for c, tile in enumerate(row):
                x = c * TILE_SIZE
                y = (height - r - 1) * TILE_SIZE

                if tile == 1:
                    # 牆
                    w = arcade.Sprite(str(wall_img), wall_scale)
                    w.center_x = x + TILE_SIZE / 2
                    w.center_y = y + TILE_SIZE / 2
                    self.walls.append(w)

                elif tile == 2:
                    # 一般豆子
                    self.pellets.append(Pellet(x, y))
                    empty.append((x, y))

                elif tile == 3:
                    # Power Pellet
                    self.power_pellets.append(PowerPellet(x, y))
                    empty.append((x, y))

                elif tile == 0:
                    # 純路面
                    empty.append((x, y))

        # ---------- 玩家出生點：尋找安全的起始位置 ----------
        if empty:
            # 方法 1：嘗試使用地圖左上角的空地（傳統 Pac-Man 位置）
            player_x = TILE_SIZE + TILE_SIZE / 2
            player_y = (height - 2) * TILE_SIZE + TILE_SIZE / 2
            
            # 檢查該位置是否為空地
            start_pos_is_empty = False
            for ex, ey in empty:
                if abs(ex + TILE_SIZE/2 - player_x) < 1 and abs(ey + TILE_SIZE/2 - player_y) < 1:
                    start_pos_is_empty = True
                    break
            
            # 如果左上角不是空地，就用中間位置
            if not start_pos_is_empty:
                px, py = empty[len(empty) // 2]
                player_x = px + TILE_SIZE / 2
                player_y = py + TILE_SIZE / 2
            
            self.player.center_x = player_x
            self.player.center_y = player_y
            
            print(f"[DEBUG] Player spawned at: ({self.player.center_x}, {self.player.center_y})")

        # ---------- 鬼出生點 ----------
        random.shuffle(empty)
        ghost_colors = ["red", "blue", "pink", "orange"]
        
        # 選擇遠離玩家的位置作為鬼的出生點
        ghost_positions = []
        for ex, ey in empty:
            # 計算與玩家的距離
            dist = ((ex + TILE_SIZE/2 - self.player.center_x) ** 2 + 
                   (ey + TILE_SIZE/2 - self.player.center_y) ** 2) ** 0.5
            ghost_positions.append((dist, ex, ey))
        
        # 按距離排序，選擇較遠的位置
        ghost_positions.sort(reverse=True)
        self.ghost_spawn_points = [(x, y) for _, x, y in ghost_positions[:len(ghost_colors)]]

        for color, (gx, gy) in zip(ghost_colors, self.ghost_spawn_points):
            g = Ghost(gx, gy, color)
            g.validate_and_set_direction(self.walls)
            self.ghosts.append(g)
            print(f"[DEBUG] Ghost {color} spawned at: ({g.center_x}, {g.center_y})")

    # ---------------- 鍵盤控制（給 main.py 呼叫） ----------------

    def on_key_press(self, key, modifiers):
        """把方向鍵 / WASD 轉換成 Player 的下一步方向"""
        if key in (arcade.key.UP, arcade.key.W):
            self.player.next_change_x = 0
            self.player.next_change_y = 1
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.player.next_change_x = 0
            self.player.next_change_y = -1
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.player.next_change_x = -1
            self.player.next_change_y = 0
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player.next_change_x = 1
            self.player.next_change_y = 0

    # ---------------- 可被子類覆寫的行為 ----------------

    def handle_ghost_eaten(self, ghost):
        ghost.remove_from_sprite_lists()
        self.score += 200

    def handle_pellet_eaten(self, p):
        p.remove_from_sprite_lists()
        self.score += 10

    def handle_power_pellet_eaten(self, p):
        p.remove_from_sprite_lists()
        self.score += 50
        for g in self.ghosts:
            g.set_frightened()

    def check_post_update(self):
        """Classic / Endless / Wave 在這裡做自己的勝利條件"""
        return

    # ---------------- 主更新迴圈 ----------------

    def update(self, dt):
        if self.finished:
            return

        # 玩家移動
        self.player.update_movement(self.walls)
        # Power Pellet 動畫
        self.power_pellets.update()

        # 鬼 AI & 碰撞
        for g in self.ghosts:
            g.update_ai(
                self.walls,
                self.player.center_x,
                self.player.center_y,
                self.player.change_x,
                self.player.change_y,
            )

            if arcade.check_for_collision(self.player, g):
                if g.state == "frightened":
                    self.handle_ghost_eaten(g)
                    continue  # 改用 continue 而非 return
                if g.state != "eaten":
                    self.result = "GAME_OVER"
                    self.finished = True
                    return

        # 吃豆子
        for p in arcade.check_for_collision_with_list(self.player, self.pellets):
            self.handle_pellet_eaten(p)

        # 吃 Power Pellet
        for p in arcade.check_for_collision_with_list(self.player, self.power_pellets):
            self.handle_power_pellet_eaten(p)

        # 模式特化檢查（Victory / 換 Wave 等）
        self.check_post_update()

    # ---------------- 繪圖 ----------------

    def draw(self):
        self.walls.draw()
        self.pellets.draw()
        self.power_pellets.draw()
        self.ghosts.draw()
        self.player_list.draw()
        
        