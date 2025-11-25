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

        # 地圖 / 導航格子
        self.map = None
        self.nav_grid = None
        self.grid_width = 0
        self.grid_height = 0

        # 鬼出生點（Endless 用）
        self.ghost_spawn_points = []

        self.setup_world()

    # ---------------- 世界建立 ----------------

    def setup_world(self):
        """重新產生整張地圖和所有物件"""
        self.map = generate_map()

        # 建立 navigation grid：
        # True = 可走 / False = 牆（tile==1）
        self.grid_height = len(self.map)
        self.grid_width = len(self.map[0]) if self.map else 0
        self.nav_grid = [
            [tile != 1 for tile in row]
            for row in self.map
        ]

        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.pellets = arcade.SpriteList()
        self.power_pellets = arcade.SpriteList()
        self.ghosts = arcade.SpriteList()
        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

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

        # ---------- 玩家出生點：找一個安全起點 ----------
        if empty:
            # 預設嘗試左上角附近
            player_x = TILE_SIZE + TILE_SIZE / 2
            player_y = (height - 2) * TILE_SIZE + TILE_SIZE / 2

            start_pos_is_empty = False
            for ex, ey in empty:
                if abs(ex + TILE_SIZE / 2 - player_x) < 1 and abs(ey + TILE_SIZE / 2 - player_y) < 1:
                    start_pos_is_empty = True
                    break

            if not start_pos_is_empty:
                px, py = empty[len(empty) // 2]
                player_x = px + TILE_SIZE / 2
                player_y = py + TILE_SIZE / 2

            self.player.center_x = player_x
            self.player.center_y = player_y

        # ---------- 鬼出生點 ----------
        random.shuffle(empty)
        ghost_colors = ["red", "blue", "pink", "orange"]

        ghost_positions = []
        for ex, ey in empty:
            dist = ((ex + TILE_SIZE / 2 - self.player.center_x) ** 2 +
                    (ey + TILE_SIZE / 2 - self.player.center_y) ** 2) ** 0.5
            ghost_positions.append((dist, ex, ey))

        ghost_positions.sort(reverse=True)
        self.ghost_spawn_points = [(x, y) for _, x, y in ghost_positions[:len(ghost_colors)]]

        for color, (gx, gy) in zip(ghost_colors, self.ghost_spawn_points):
            g = Ghost(gx, gy, color)
            g.validate_and_set_direction(self.walls)

            # 給鬼導覽格資料，用於 BFS 尋路與 AI
            g.nav_grid = self.nav_grid
            g.grid_width = self.grid_width
            g.grid_height = self.grid_height

            self.ghosts.append(g)

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
            # 把所有鬼的列表給 AI，做團隊戰術 + Anti-grouping 用
            g._all_ghosts = self.ghosts

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
                    continue
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
