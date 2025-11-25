import arcade
import random
import os
import time
from collections import deque

from constants import GHOST_SPEED, TILE_SIZE
from character import autoscale


class Ghost(arcade.Sprite):
    """
    強化版鬼魂 AI：
    - 基本狀態：chase / scatter / patrol / random_walk
    - 個性：red=aggressive, pink=ambush, blue=flanking, orange=shy
    - BFS 尋路：找最短路徑
    - Strategic Diversity System：不同顏色走不同變體路線 → 不再全部擠同一條路
    - Anti-grouping：太靠近其他鬼會刻意分散
    - Stuck detection：偵測在同區域打轉並強制改策略
    """

    def __init__(self, x, y, color: str = "red"):
        base = os.path.dirname(__file__)
        img = os.path.join(base, "assets", f"ghost_{color}.png")

        scale = autoscale(img, TILE_SIZE)
        super().__init__(img, scale)

        # 放在格子中心
        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2

        # 初始方向
        direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.change_x = direction[0]
        self.change_y = direction[1]

        self.speed = GHOST_SPEED
        self.ghost_color = color

        # 狀態
        self.state = "chase"  # chase / frightened / eaten
        self.frightened_timer = 0
        self.frightened_duration = 600  # 10 秒（60 FPS）

        # AI 模式
        self.ai_mode = "chase"  # chase / scatter / patrol / random_walk
        self.mode_change_timer = random.randint(120, 300)
        self.patrol_target = None

        # 個性（行為風格）
        self.personality = {
            "red": "aggressive",
            "pink": "ambush",
            "blue": "flanking",
            "orange": "shy",
        }.get(color, "aggressive")

        # 顏色偏移：避免所有鬼鎖同一格
        offsets = {
            "red": (0, 0),
            "pink": (2 * TILE_SIZE, 2 * TILE_SIZE),
            "blue": (-3 * TILE_SIZE, 2 * TILE_SIZE),
            "orange": (0, -3 * TILE_SIZE),
        }
        self.target_offset = offsets.get(color, (0, 0))

        # 噪音與隨機性
        self.noise_offset = random.uniform(0, 1000)
        self.current_randomness = random.uniform(0.2, 0.5)

        # Anti-grouping / stuck detection
        self.avoid_radius = TILE_SIZE * 3
        self.recent_positions = []
        self.stuck_counter = 0
        self.position_check_interval = 15

        # BFS 用的導覽格
        self.nav_grid = None
        self.grid_width = 0
        self.grid_height = 0

        # 由 BaseMode 塞進來的鬼群列表（團隊戰術 / anti-grouping 用）
        self._all_ghosts = None

    # ------------------------------------------------------------------
    # 工具：Grid / BFS
    # ------------------------------------------------------------------
    def _world_to_grid(self, x: float, y: float):
        """世界座標 → (row, col)，row 0 在最上方。"""
        if self.grid_height == 0 or self.grid_width == 0:
            return None

        col = int(x // TILE_SIZE)
        row_from_bottom = int(y // TILE_SIZE)
        row = self.grid_height - 1 - row_from_bottom

        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            return row, col
        return None

    def _grid_to_world(self, row: int, col: int):
        """(row, col) → 世界座標中心點。"""
        x = col * TILE_SIZE + TILE_SIZE / 2
        y = (self.grid_height - 1 - row) * TILE_SIZE + TILE_SIZE / 2
        return x, y

    def _bfs_next_world(self, start_x: float, start_y: float,
                        target_x: float, target_y: float):
        """標準 BFS，回傳從起點到目標路徑中的下一步世界座標。"""
        if self.nav_grid is None:
            return None

        start_rc = self._world_to_grid(start_x, start_y)
        target_rc = self._world_to_grid(target_x, target_y)
        if start_rc is None or target_rc is None:
            return None

        sr, sc = start_rc
        tr, tc = target_rc

        # 目標如果是牆就放棄
        if not self.nav_grid[tr][tc]:
            return None

        q = deque()
        q.append((sr, sc))
        visited = {(sr, sc)}
        parent = {}

        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上下左右

        found = False
        while q:
            r, c = q.popleft()
            if (r, c) == (tr, tc):
                found = True
                break

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < self.grid_height and 0 <= nc < self.grid_width):
                    continue
                if not self.nav_grid[nr][nc]:
                    continue
                if (nr, nc) in visited:
                    continue
                visited.add((nr, nc))
                parent[(nr, nc)] = (r, c)
                q.append((nr, nc))

        if not found:
            return None

        # 回溯路徑
        path = []
        cur = (tr, tc)
        while cur != (sr, sc):
            path.append(cur)
            cur = parent[cur]
        path.append((sr, sc))
        path.reverse()

        if len(path) < 2:
            return None

        nr, nc = path[1]
        return self._grid_to_world(nr, nc)

    def _choose_path_variant(self, sx: float, sy: float,
                             tx: float, ty: float):
        """
        Strategic Diversity：
        同樣的目標 (tx, ty)，不同顏色選擇不同變體路線，
        避免大家都走完全一樣的 BFS path。
        """
        # baseline：最短路徑
        base_next = self._bfs_next_world(sx, sy, tx, ty)

        # 紅鬼：永遠使用最短路
        if self.ghost_color == "red":
            return base_next

        # 藍鬼：偏移目標一格，選擇「第二種」逼近方式
        if self.ghost_color == "blue":
            if base_next is None:
                return None
            offset = random.choice([
                (TILE_SIZE, 0),
                (-TILE_SIZE, 0),
                (0, TILE_SIZE),
                (0, -TILE_SIZE),
            ])
            tx2, ty2 = tx + offset[0], ty + offset[1]
            alt_next = self._bfs_next_world(sx, sy, tx2, ty2)
            return alt_next or base_next

        # 粉鬼：偏好弧線路徑，部份時間使用「斜向目標」
        if self.ghost_color == "pink":
            if random.random() < 0.4:
                alt = random.choice([
                    (TILE_SIZE, TILE_SIZE),
                    (-TILE_SIZE, TILE_SIZE),
                    (TILE_SIZE, -TILE_SIZE),
                    (-TILE_SIZE, -TILE_SIZE),
                ])
                tx2, ty2 = tx + alt[0], ty + alt[1]
                alt_next = self._bfs_next_world(sx, sy, tx2, ty2)
                return alt_next or base_next
            return base_next

        # 橘鬼：50% 時間不使用 BFS，維持原「亂走+追蹤」特性
        if self.ghost_color == "orange":
            if random.random() < 0.5:
                return None
            return base_next

        return base_next

    # ------------------------------------------------------------------
    # 其他工具
    # ------------------------------------------------------------------
    def validate_and_set_direction(self, walls):
        """Validate initial direction and pick a valid one if needed"""
        old_x, old_y = self.center_x, self.center_y
        test_x = self.center_x + self.change_x * TILE_SIZE
        test_y = self.center_y + self.change_y * TILE_SIZE

        self.center_x = test_x
        self.center_y = test_y

        if not arcade.check_for_collision_with_list(self, walls):
            self.center_x, self.center_y = old_x, old_y
            return

        self.center_x, self.center_y = old_x, old_y
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            test_x = old_x + dx * TILE_SIZE
            test_y = old_y + dy * TILE_SIZE
            self.center_x = test_x
            self.center_y = test_y

            if not arcade.check_for_collision_with_list(self, walls):
                self.center_x, self.center_y = old_x, old_y
                self.change_x, self.change_y = dx, dy
                return

        self.center_x, self.center_y = old_x, old_y
        self.change_x, self.change_y = 0, 0

    def set_frightened(self):
        """進入驚嚇狀態（可被吃）"""
        self.state = "frightened"
        self.frightened_timer = self.frightened_duration
        self.alpha = 150

    def simple_noise(self, x, y):
        """簡單的偽隨機噪聲函數"""
        val = ((x * 12.9898 + y * 78.233 + self.noise_offset) * 43758.5453)
        return (val - int(val)) * 2 - 1  # -1 ~ 1

    def get_scatter_target(self):
        """獲取散開模式的目標（地圖角落）"""
        corners = [
            (2 * TILE_SIZE, 2 * TILE_SIZE),
            (17 * TILE_SIZE, 2 * TILE_SIZE),
            (2 * TILE_SIZE, 19 * TILE_SIZE),
            (17 * TILE_SIZE, 19 * TILE_SIZE),
        ]
        corner_index = {
            "red": 0,
            "pink": 1,
            "blue": 2,
            "orange": 3,
        }.get(self.ghost_color, 0)
        return corners[corner_index]

    def _find_red_leader(self):
        """在 _all_ghosts 中找到紅鬼（leader），用於團隊包抄戰術"""
        if not self._all_ghosts:
            return None
        for g in self._all_ghosts:
            try:
                if g.ghost_color == "red":
                    return g
            except AttributeError:
                continue
        return None

    # ------------------------------------------------------------------
    # 目標決策
    # ------------------------------------------------------------------
    def get_target_position(self, player_x, player_y, player_dx, player_dy):
        """根據AI模式和個性選擇目標位置"""
        # 模式切換計時器
        self.mode_change_timer -= 1
        if self.mode_change_timer <= 0:
            modes = ["chase", "scatter", "patrol", "random_walk"]
            weights = [0.4, 0.2, 0.2, 0.2]
            self.ai_mode = random.choices(modes, weights=weights)[0]
            self.mode_change_timer = random.randint(120, 300)
            self.patrol_target = None

            # 偶爾改變隨機性
            if random.random() < 0.3:
                self.current_randomness = random.uniform(0.2, 0.6)

        target_x, target_y = player_x, player_y

        # --- 模式判斷 ---
        if self.ai_mode == "scatter":
            target_x, target_y = self.get_scatter_target()

        elif self.ai_mode == "patrol":
            if self.patrol_target is None or random.random() < 0.01:
                self.patrol_target = (
                    random.randint(2, 17) * TILE_SIZE,
                    random.randint(2, 19) * TILE_SIZE,
                )
            target_x, target_y = self.patrol_target

        elif self.ai_mode == "random_walk":
            t = time.time() * 0.5
            noise_x = self.simple_noise(t, 0) * 10
            noise_y = self.simple_noise(0, t) * 10
            target_x = self.center_x + noise_x * TILE_SIZE
            target_y = self.center_y + noise_y * TILE_SIZE

        else:  # chase 模式，套個性
            if self.personality == "aggressive":
                target_x, target_y = player_x, player_y

            elif self.personality == "ambush":
                target_x = player_x + player_dx * 4 * TILE_SIZE
                target_y = player_y + player_dy * 4 * TILE_SIZE

            elif self.personality == "flanking":
                leader = self._find_red_leader()
                if leader is not None:
                    lx, ly = leader.center_x, leader.center_y
                    target_x = 2 * player_x - lx
                    target_y = 2 * player_y - ly
                else:
                    offset_x = player_x - self.center_x
                    offset_y = player_y - self.center_y
                    target_x = player_x + offset_x * 0.5
                    target_y = player_y + offset_y * 0.5

            elif self.personality == "shy":
                dist = ((self.center_x - player_x) ** 2 + (self.center_y - player_y) ** 2) ** 0.5
                if dist < 8 * TILE_SIZE:
                    target_x = self.center_x - (player_x - self.center_x)
                    target_y = self.center_y - (player_y - self.center_y)
                else:
                    target_x, target_y = player_x, player_y

        # 最後加顏色偏移 → 讓鬼目標不完全重疊
        target_x += self.target_offset[0]
        target_y += self.target_offset[1]
        return target_x, target_y

    # ------------------------------------------------------------------
    # 主 AI 更新
    # ------------------------------------------------------------------
    def update_ai(self, walls, player_x, player_y, player_dx, player_dy):
        """混合AI系統 - 結合多種行為模式 + BFS + 路線分化"""
        # frightened 計時
        if self.state == "frightened":
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = "chase"
                self.alpha = 255

        # 嘗試往目前方向前進
        new_x = self.center_x + self.change_x * self.speed
        new_y = self.center_y + self.change_y * self.speed

        old_x, old_y = self.center_x, self.center_y
        self.center_x = new_x
        self.center_y = new_y

        hit_wall = arcade.check_for_collision_with_list(self, walls)

        # 先取得目標位置
        if self.state == "frightened":
            # 驚嚇時完全隨機逃跑
            target_x = self.center_x + random.randint(-5, 5) * TILE_SIZE
            target_y = self.center_y + random.randint(-5, 5) * TILE_SIZE
        else:
            target_x, target_y = self.get_target_position(player_x, player_y, player_dx, player_dy)

        if hit_wall:
            # 碰牆 → 回到原點並重新決策方向
            self.center_x, self.center_y = old_x, old_y

            used_bfs = False
            # 非驚嚇狀態且有 nav_grid → 優先使用路徑搜尋（含分化）
            if self.state != "frightened" and self.nav_grid is not None:
                next_world = self._choose_path_variant(old_x, old_y, target_x, target_y)
                if next_world is not None:
                    nx, ny = next_world
                    dx = nx - old_x
                    dy = ny - old_y
                    if abs(dx) > abs(dy):
                        self.change_x = 1 if dx > 0 else -1
                        self.change_y = 0
                    else:
                        self.change_y = 1 if dy > 0 else -1
                        self.change_x = 0
                    used_bfs = True

            # BFS 失敗 / 驚嚇狀態 → 回到原本四方向測試 + 加權隨機
            if not used_bfs:
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                valid_moves = []

                for dx, dy in directions:
                    if dx == -self.change_x and dy == -self.change_y:
                        continue

                    test_x = old_x + dx * self.speed * 2
                    test_y = old_y + dy * self.speed * 2

                    self.center_x = test_x
                    self.center_y = test_y

                    if not arcade.check_for_collision_with_list(self, walls):
                        valid_moves.append((dx, dy))

                    self.center_x, self.center_y = old_x, old_y

                if not valid_moves:
                    valid_moves = [(-self.change_x, -self.change_y)]

                if valid_moves:
                    rand = random.random()
                    if self.state == "frightened" or rand < self.current_randomness:
                        self.change_x, self.change_y = random.choice(valid_moves)
                    else:
                        weights = []
                        for dx, dy in valid_moves:
                            next_x = old_x + dx * TILE_SIZE
                            next_y = old_y + dy * TILE_SIZE
                            dist = ((next_x - target_x) ** 2 + (next_y - target_y) ** 2) ** 0.5
                            noise = self.simple_noise(next_x * 0.01, next_y * 0.01) * 0.5 + 0.5
                            weight = (1.0 / (dist + 1)) * (0.5 + noise)
                            weights.append(weight)

                        total_weight = sum(weights)
                        if total_weight > 0:
                            rand_val = random.uniform(0, total_weight)
                            cumulative = 0
                            for i, weight in enumerate(weights):
                                cumulative += weight
                                if rand_val <= cumulative:
                                    self.change_x, self.change_y = valid_moves[i]
                                    break
                        else:
                            self.change_x, self.change_y = random.choice(valid_moves)

            # Anti-grouping：避免多隻鬼長時間重疊
            if self._all_ghosts:
                for other in self._all_ghosts:
                    if other is self:
                        continue
                    dist = ((self.center_x - other.center_x) ** 2 +
                            (self.center_y - other.center_y) ** 2) ** 0.5
                    if dist < self.avoid_radius:
                        if random.random() < 0.6:
                            self.ai_mode = random.choice(["scatter", "patrol", "random_walk"])
                            self.mode_change_timer = random.randint(60, 180)
                        break

            self._check_if_stuck(old_x, old_y)

    # ------------------------------------------------------------------
    # 困住檢測
    # ------------------------------------------------------------------
    def _check_if_stuck(self, x, y):
        """檢測鬼是否在同一小區域重複移動"""
        grid_pos = (int(x // TILE_SIZE), int(y // TILE_SIZE))

        self.recent_positions.append(grid_pos)
        if len(self.recent_positions) > 10:
            self.recent_positions.pop(0)

        if len(self.recent_positions) >= 10 and random.randint(0, self.position_check_interval) == 0:
            unique_positions = len(set(self.recent_positions))

            if unique_positions <= 3:
                self.stuck_counter += 1

                if self.stuck_counter >= 2:
                    self.ai_mode = random.choice(["scatter", "random_walk"])
                    self.current_randomness = random.uniform(0.5, 0.8)
                    self.mode_change_timer = random.randint(60, 120)
                    self.stuck_counter = 0
                    self.recent_positions.clear()
                    print(f"{self.ghost_color} ghost detected stuck! Forcing mode change.")
            else:
                self.stuck_counter = max(0, self.stuck_counter - 1)
