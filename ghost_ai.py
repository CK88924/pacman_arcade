import arcade
import random
import os
import time
from collections import deque
from constants import GHOST_SPEED, TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from character import autoscale


class Ghost(arcade.Sprite):
    def __init__(self, x, y, color="red"):
        base = os.path.dirname(__file__)
        img = os.path.join(base, "assets", f"ghost_{color}.png")

        scale = autoscale(img, TILE_SIZE)
        super().__init__(img, scale)

        # 起始位置（像 Ghost House）
        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2
        self.home_x = self.center_x
        self.home_y = self.center_y

        # 初始方向
        direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.change_x = direction[0]
        self.change_y = direction[1]

        self.speed = GHOST_SPEED
        self.ghost_color = color

        # 狀態：chase / frightened / eaten
        self.state = "chase"
        self.frightened_timer = 0
        self.frightened_duration = 600  # 10 秒（60FPS 假設）

        # 被吃掉後的重生計時
        self.respawn_timer = 0

        # 混合 AI 模式
        self.ai_mode = "chase"  # chase, scatter, patrol, random_walk
        self.mode_change_timer = random.randint(120, 300)
        self.patrol_target = None
        self.random_walk_timer = 0

        # 個性
        self.personality = {
            "red": "aggressive",
            "pink": "ambush",
            "blue": "flanking",
            "orange": "shy"
        }.get(color, "aggressive")

        # 噪聲與隨機性
        self.noise_offset = random.uniform(0, 1000)
        self.current_randomness = random.uniform(0.2, 0.5)

        # 反覆路徑偵測（Ghost Memory）
        self.recent_positions = []   # 最近 10 個格子
        self.stuck_counter = 0       # 疑似 loop 次數
        self.position_check_interval = 15  # 每 15 frame 檢查一次

    # ------------------------------------------------------------
    # 初始化方向檢查
    # ------------------------------------------------------------
    def validate_and_set_direction(self, walls):
        """確保一開始的移動方向不是撞牆的。"""
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

    # ------------------------------------------------------------
    # 狀態控制
    # ------------------------------------------------------------
    def set_frightened(self):
        """進入可被吃狀態（Power Pellet）"""
        # 如果已經是 eaten，就不用再變
        if self.state == "eaten":
            return
        self.state = "frightened"
        self.frightened_timer = self.frightened_duration
        self.alpha = 150

    def on_eaten(self):
        """被玩家吃掉：進入死亡狀態，稍後回 Ghost House 重生。"""
        self.state = "eaten"
        self.respawn_timer = 120  # 約 2 秒
        self.alpha = 0            # 先隱形
        self.change_x = 0
        self.change_y = 0

    # ------------------------------------------------------------
    # 工具：噪聲 & 目標點
    # ------------------------------------------------------------
    def simple_noise(self, x, y):
        val = ((x * 12.9898 + y * 78.233 + self.noise_offset) * 43758.5453)
        return (val - int(val)) * 2 - 1

    def get_scatter_target(self):
        corners = [
            (2 * TILE_SIZE, 2 * TILE_SIZE),
            (17 * TILE_SIZE, 2 * TILE_SIZE),
            (2 * TILE_SIZE, 19 * TILE_SIZE),
            (17 * TILE_SIZE, 19 * TILE_SIZE)
        ]
        index = {"red": 0, "pink": 1, "blue": 2, "orange": 3}.get(self.ghost_color, 0)
        return corners[index]

    def get_target_position(self, px, py, dx, dy):
        """依模式 + 個性選追擊目標。"""
        self.mode_change_timer -= 1
        if self.mode_change_timer <= 0:
            modes = ["chase", "scatter", "patrol", "random_walk"]
            self.ai_mode = random.choice(modes)
            self.mode_change_timer = random.randint(120, 300)
            self.patrol_target = None

            if random.random() < 0.3:
                self.current_randomness = random.uniform(0.2, 0.6)

        if self.ai_mode == "scatter":
            return self.get_scatter_target()

        elif self.ai_mode == "patrol":
            if not self.patrol_target or random.random() < 0.02:
                self.patrol_target = (
                    random.randint(2, 17) * TILE_SIZE,
                    random.randint(2, 19) * TILE_SIZE
                )
            return self.patrol_target

        elif self.ai_mode == "random_walk":
            t = time.time() * 0.35
            noise_x = self.simple_noise(t, 0) * 8
            noise_y = self.simple_noise(0, t) * 8
            return self.center_x + noise_x * TILE_SIZE, self.center_y + noise_y * TILE_SIZE

        # chase 根據個性
        if self.personality == "aggressive":
            return px, py

        elif self.personality == "ambush":
            return px + dx * 4 * TILE_SIZE, py + dy * 4 * TILE_SIZE

        elif self.personality == "flanking":
            return px + (px - self.center_x) * 0.4, py + (py - self.center_y) * 0.4

        elif self.personality == "shy":
            dist = ((self.center_x - px) ** 2 + (self.center_y - py) ** 2) ** 0.5
            if dist < 7 * TILE_SIZE:
                return self.center_x - (px - self.center_x), self.center_y - (py - self.center_y)
            else:
                return px, py

        return px, py

    # ------------------------------------------------------------
    # Smart Loop Escape（用 BFS 找一個朝玩家方向的脫困方向）
    # ------------------------------------------------------------
    def _escape_loop(self, walls, px, py):
        """使用 BFS 找一個朝玩家方向的下一步方向（只在被判定 loop 時觸發）"""
        grid_w = SCREEN_WIDTH // TILE_SIZE
        grid_h = SCREEN_HEIGHT // TILE_SIZE

        # 牆 → blocked set
        blocked = set()
        for w in walls:
            gx = int(w.center_x // TILE_SIZE)
            gy = int(w.center_y // TILE_SIZE)
            blocked.add((gx, gy))

        start = (int(self.center_x // TILE_SIZE), int(self.center_y // TILE_SIZE))
        target = (int(px // TILE_SIZE), int(py // TILE_SIZE))

        if start in blocked:
            blocked.remove(start)

        q = deque([start])
        prev = {start: None}
        found = False

        while q:
            cx, cy = q.popleft()
            if (cx, cy) == target:
                found = True
                break

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < grid_w and
                    0 <= ny < grid_h and
                    (nx, ny) not in blocked and
                    (nx, ny) not in prev
                ):
                    prev[(nx, ny)] = (cx, cy)
                    q.append((nx, ny))

        if not found:
            # 找不到玩家路徑時，用本地 heuristic 退而求其次
            best_move = None
            best_score = -9999
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                test_x = self.center_x + dx * TILE_SIZE
                test_y = self.center_y + dy * TILE_SIZE

                old_x, old_y = self.center_x, self.center_y
                self.center_x, self.center_y = test_x, test_y
                hit = arcade.check_for_collision_with_list(self, walls)
                self.center_x, self.center_y = old_x, old_y

                if not hit:
                    score = abs(dx) + abs(dy) + random.random()
                    if score > best_score:
                        best_score = score
                        best_move = (dx, dy)

            if best_move:
                self.change_x, self.change_y = best_move
            return

        # 回溯 BFS 路徑
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        if len(path) < 2:
            return

        first, second = path[0], path[1]
        step_dx = second[0] - first[0]
        step_dy = second[1] - first[1]

        self.change_x = step_dx
        self.change_y = step_dy
        self.center_x = first[0] * TILE_SIZE + TILE_SIZE / 2
        self.center_y = first[1] * TILE_SIZE + TILE_SIZE / 2

    # ------------------------------------------------------------
    # 主要更新邏輯
    # ------------------------------------------------------------
    def update_ai(self, walls, px, py, dx, dy):
        # 狀態：eaten → 等待 respawn → 回家 → 重新 chase
        if self.state == "eaten":
            if self.respawn_timer > 0:
                self.respawn_timer -= 1
                return
            else:
                # 復活：回 Ghost House
                self.center_x = self.home_x
                self.center_y = self.home_y
                self.state = "chase"
                self.alpha = 255
                self.validate_and_set_direction(walls)
                return

        # frightened 倒數
        if self.state == "frightened":
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = "chase"
                self.alpha = 255

        # 嘗試往前走
        new_x = self.center_x + self.change_x * self.speed
        new_y = self.center_y + self.change_y * self.speed

        old_x, old_y = self.center_x, self.center_y
        self.center_x, self.center_y = new_x, new_y

        if arcade.check_for_collision_with_list(self, walls):
            # 撞牆 → 回到舊位置並重新選方向
            self.center_x, self.center_y = old_x, old_y
            self.pick_direction(walls, px, py, dx, dy)

        # 檢查是否在小範圍 loop
        self._check_if_stuck(old_x, old_y, walls, px, py)

    def pick_direction(self, walls, px, py, dx, dy):
        """選方向：混合「追目標 + 隨機」並加入動態 backtracking 規則。"""
        target_x, target_y = self.get_target_position(px, py, dx, dy)

        possible = []
        for d_x, d_y in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            # 動態 backtracking：
            # 正常時禁止「直接掉頭」；但當 stuck_counter > 0 時允許掉頭幫助脫困
            if self.stuck_counter == 0 and d_x == -self.change_x and d_y == -self.change_y:
                continue

            test_x = self.center_x + d_x * TILE_SIZE
            test_y = self.center_y + d_y * TILE_SIZE

            old_x, old_y = self.center_x, self.center_y
            self.center_x, self.center_y = test_x, test_y
            blocked = arcade.check_for_collision_with_list(self, walls)
            self.center_x, self.center_y = old_x, old_y

            if not blocked:
                possible.append((d_x, d_y))

        if not possible:
            return

        # 部分隨機，部分朝目標
        if random.random() < self.current_randomness or self.state == "frightened":
            self.change_x, self.change_y = random.choice(possible)
        else:
            best = min(
                possible,
                key=lambda d: (
                    abs((self.center_x + d[0] * TILE_SIZE) - target_x) +
                    abs((self.center_y + d[1] * TILE_SIZE) - target_y)
                )
            )
            self.change_x, self.change_y = best

    # ------------------------------------------------------------
    # Loop 偵測（Ghost Memory）
    # ------------------------------------------------------------
    def _check_if_stuck(self, x, y, walls, px, py):
        """檢測是否在同一小區域繞圈；必要時啟用 Smart Loop Escape。"""
        grid = (int(x // TILE_SIZE), int(y // TILE_SIZE))
        self.recent_positions.append(grid)

        if len(self.recent_positions) > 10:
            self.recent_positions.pop(0)

        # 每一段時間檢查一次
        if len(self.recent_positions) >= 10 and random.randint(0, self.position_check_interval) == 0:
            unique_count = len(set(self.recent_positions))

            # 10 筆紀錄中只有 <=3 格子 → 判定為 loop
            if unique_count <= 3:
                self.stuck_counter += 1

                if self.stuck_counter >= 2:
                    # 啟動 Smart Loop Escape（使用 BFS 朝玩家方向脫困）
                    print(f"[AI] {self.ghost_color} detected loop → escaping")
                    self._escape_loop(walls, px, py)
                    self.stuck_counter = 0
                    self.recent_positions.clear()
            else:
                # loop 消失 → 慢慢降回 0
                self.stuck_counter = max(0, self.stuck_counter - 1)
