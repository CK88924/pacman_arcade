import arcade
import random
import os
import time
from constants import GHOST_SPEED, TILE_SIZE
from character import autoscale


class Ghost(arcade.Sprite):
    def __init__(self, x, y, color="red"):
        base = os.path.dirname(__file__)
        img = os.path.join(base, "assets", f"ghost_{color}.png")

        scale = autoscale(img, TILE_SIZE)
        super().__init__(img, scale)

        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2
        
        # Start with random direction
        direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.change_x = direction[0]
        self.change_y = direction[1]
        
        self.speed = GHOST_SPEED
        self.ghost_color = color
        
        # Ghost AI states
        self.state = "chase"
        self.frightened_timer = 0
        self.frightened_duration = 600  # 10 seconds at 60 FPS
        
        # 混合AI系統
        self.ai_mode = "chase"  # chase, scatter, patrol, random_walk
        self.mode_change_timer = random.randint(120, 300)  # 2-5秒切換模式
        self.patrol_target = None
        self.random_walk_timer = 0
        
        # AI personality based on color
        self.personality = {
            "red": "aggressive",
            "pink": "ambush",
            "blue": "flanking",
            "orange": "shy"
        }.get(color, "aggressive")
        
        # 用於生成不可預測行為的噪聲
        self.noise_offset = random.uniform(0, 1000)
        
        # 動態隨機性 - 定期變化
        self.current_randomness = random.uniform(0.2, 0.5)  # 當前的隨機性程度
        
        # 困住檢測系統
        self.recent_positions = []  # 最近10個位置
        self.stuck_counter = 0  # 困住計數器
        self.position_check_interval = 15  # 每15幀檢查一次
    
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
        # 使用sin/cos混合生成平滑的偽隨機值
        val = (
            (x * 12.9898 + y * 78.233 + self.noise_offset) * 43758.5453
        )
        return (val - int(val)) * 2 - 1  # 返回 -1 到 1

    def get_scatter_target(self):
        """獲取散開模式的目標（地圖角落）"""
        corners = [
            (2 * TILE_SIZE, 2 * TILE_SIZE),
            (17 * TILE_SIZE, 2 * TILE_SIZE),
            (2 * TILE_SIZE, 19 * TILE_SIZE),
            (17 * TILE_SIZE, 19 * TILE_SIZE)
        ]
        # 根據鬼的顏色選擇不同角落
        corner_index = {"red": 0, "pink": 1, "blue": 2, "orange": 3}.get(self.ghost_color, 0)
        return corners[corner_index]

    def get_target_position(self, player_x, player_y, player_dx, player_dy):
        """根據AI模式和個性選擇目標位置"""
        # 模式切換計時器
        self.mode_change_timer -= 1
        if self.mode_change_timer <= 0:
            # 隨機切換模式
            modes = ["chase", "scatter", "patrol", "random_walk"]
            weights = [0.4, 0.2, 0.2, 0.2]  # chase最常見
            self.ai_mode = random.choices(modes, weights=weights)[0]
            self.mode_change_timer = random.randint(120, 300)
            self.patrol_target = None
            
            # 隨機改變多樣性偏好
            if random.random() < 0.3:  # 30%機率大幅改變隨機性
                self.current_randomness = random.uniform(0.2, 0.6)
        
        # 根據模式選擇目標
        if self.ai_mode == "scatter":
            return self.get_scatter_target()
        
        elif self.ai_mode == "patrol":
            if self.patrol_target is None or random.random() < 0.01:
                # 選擇新的巡邏目標（隨機地圖位置）
                self.patrol_target = (
                    random.randint(2, 17) * TILE_SIZE,
                    random.randint(2, 19) * TILE_SIZE
                )
            return self.patrol_target
        
        elif self.ai_mode == "random_walk":
            # 使用噪聲場生成隨機但平滑的目標
            t = time.time() * 0.5
            noise_x = self.simple_noise(t, 0) * 10
            noise_y = self.simple_noise(0, t) * 10
            return (
                self.center_x + noise_x * TILE_SIZE,
                self.center_y + noise_y * TILE_SIZE
            )
        
        else:  # chase mode
            # 根據個性選擇追擊目標
            if self.personality == "aggressive":
                return player_x, player_y
            elif self.personality == "ambush":
                target_x = player_x + player_dx * 4 * TILE_SIZE
                target_y = player_y + player_dy * 4 * TILE_SIZE
                return target_x, target_y
            elif self.personality == "flanking":
                offset_x = player_x - self.center_x
                offset_y = player_y - self.center_y
                target_x = player_x + offset_x * 0.5
                target_y = player_y + offset_y * 0.5
                return target_x, target_y
            elif self.personality == "shy":
                dist = ((self.center_x - player_x) ** 2 + (self.center_y - player_y) ** 2) ** 0.5
                if dist < 8 * TILE_SIZE:
                    target_x = self.center_x - (player_x - self.center_x)
                    target_y = self.center_y - (player_y - self.center_y)
                    return target_x, target_y
                else:
                    return player_x, player_y
        
        return player_x, player_y

    def update_ai(self, walls, player_x, player_y, player_dx, player_dy):
        """混合AI系統 - 結合多種行為模式"""
        # Update frightened timer
        if self.state == "frightened":
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = "chase"
                self.alpha = 255
        
        # 先嘗試往前移動
        new_x = self.center_x + self.change_x * self.speed
        new_y = self.center_y + self.change_y * self.speed
        
        old_x, old_y = self.center_x, self.center_y
        self.center_x = new_x
        self.center_y = new_y
        
        hit_wall = arcade.check_for_collision_with_list(self, walls)
        
        if hit_wall:
            self.center_x, self.center_y = old_x, old_y
            
            # 獲取目標位置
            if self.state == "frightened":
                # 驚嚇時完全隨機
                target_x = self.center_x + random.randint(-5, 5) * TILE_SIZE
                target_y = self.center_y + random.randint(-5, 5) * TILE_SIZE
            else:
                target_x, target_y = self.get_target_position(player_x, player_y, player_dx, player_dy)
            
            # 嘗試所有4個方向
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(directions)  # 隨機順序增加變化
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
            
            # 選擇方向 - 混合策略
            if valid_moves:
                # 使用動態隨機性
                rand = random.random()
                
                if self.state == "frightened" or rand < self.current_randomness:
                    # 30% 完全隨機
                    self.change_x, self.change_y = random.choice(valid_moves)
                else:
                    # 70% 傾向目標，但用加權隨機
                    weights = []
                    for dx, dy in valid_moves:
                        next_x = old_x + dx * TILE_SIZE
                        next_y = old_y + dy * TILE_SIZE
                        dist = ((next_x - target_x) ** 2 + (next_y - target_y) ** 2) ** 0.5
                        
                        # 距離越近權重越高，但加入噪聲
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
            
            # 檢測是否困住
            self._check_if_stuck(old_x, old_y)
    
    def _check_if_stuck(self, x, y):
        """檢測鬼是否在同一小區域重複移動"""
        grid_pos = (int(x // TILE_SIZE), int(y // TILE_SIZE))
        
        # 添加當前位置
        self.recent_positions.append(grid_pos)
        if len(self.recent_positions) > 10:
            self.recent_positions.pop(0)
        
        # 每15幀檢查一次是否困住
        if len(self.recent_positions) >= 10 and random.randint(0, self.position_check_interval) == 0:
            # 計算位置的唯一性
            unique_positions = len(set(self.recent_positions))
            
            # 如果10個位置中只有3個或更少的不同位置，表示困住了
            if unique_positions <= 3:
                self.stuck_counter += 1
                
                if self.stuck_counter >= 2:  # 連續2次檢測到困住
                    # 強制改變策略
                    self.ai_mode = random.choice(["scatter", "random_walk"])
                    self.current_randomness = random.uniform(0.5, 0.8)  # 大幅提高隨機性
                    self.mode_change_timer = random.randint(60, 120)  # 短時間後再切換
                    self.stuck_counter = 0
                    self.recent_positions.clear()
                    print(f"{self.ghost_color} ghost detected stuck! Forcing mode change.")
            else:
                self.stuck_counter = max(0, self.stuck_counter - 1)  # 逐漸降低困住計數
