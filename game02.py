import pyxel
import random
import math
import json
import sys
# --- 定数の設定 ---
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
RANKING_FILE = 'ranking.txt' # ランキングファイル名

# --- ゲームシーン定数 ---
SCENE_NAME_INPUT = 0
SCENE_PLAY = 1
SCENE_GAMEOVER = 2
SCENE_LEVEL_START = 3
SCENE_GAME_CLEAR = 4

# --- ヘルパー関数: ランキング処理 ---
def load_ranking():
    """ランキングをファイルから読み込む"""
    try:
        with open(RANKING_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_ranking(ranking):
    """ランキングをファイルに保存する"""
    with open(RANKING_FILE, 'w') as f:
        json.dump(ranking, f)

def update_ranking(player_name, score):
    """ランキングを更新し、上位5件を保存する"""
    ranking = load_ranking()
    ranking.append({'name': player_name, 'score': score})
    sorted_ranking = sorted(ranking, key=lambda x: x['score'], reverse=True)
    save_ranking(sorted_ranking[:5])
    return sorted_ranking[:5]

# --- プレイヤークラス ---
class Player:
    def __init__(self):
        self.w, self.h = 8, 8
        self.x = SCREEN_WIDTH / 2 - self.w / 2
        self.y = SCREEN_HEIGHT - 20
        self.speed = 3
        self.max_hp = 100
        self.hp = self.max_hp

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x += self.speed
        if pyxel.btn(pyxel.KEY_UP):
            self.y -= self.speed
        if pyxel.btn(pyxel.KEY_DOWN):
            self.y += self.speed

        # 画面範囲の制限
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.w))
        self.y = max(SCREEN_HEIGHT * 0.75, min(self.y, SCREEN_HEIGHT - self.h))

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, 11) # GREEN

# --- 敵クラス ---
class Enemy:
    def __init__(self, pattern_type='normal'):
        self.w, self.h = 20, 16
        self.x = random.randrange(40, SCREEN_WIDTH - 40)
        self.y = 40
        self.speed_x = random.choice([-1.5, 1.5])
        self.speed_y = random.choice([-1, 1])
        self.max_hp = 200
        self.hp = self.max_hp
        self.is_alive = True

        self.pattern = pattern_type
        self.spiral_angle = 0
        if self.pattern == 'n_way':
            self.shoot_delay = 70
        elif self.pattern == 'circular':
            self.shoot_delay = 30
        elif self.pattern == 'spiral':
            self.shoot_delay = 2
        else:
            self.shoot_delay = 20
        self.shoot_timer = self.shoot_delay

    def update(self, player, bullets):
        self.x += self.speed_x
        if self.x < 0 or self.x + self.w > SCREEN_WIDTH:
            self.speed_x *= -1
        self.y += self.speed_y
        if self.y < 20 or self.y + self.h > 100:
            self.speed_y *= -1

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_delay
            px, py = player.x + player.w / 2, player.y + player.h / 2
            ex, ey = self.x + self.w / 2, self.y + self.h / 2
            
            if self.pattern == 'n_way':
                self.shoot_n_way(px, py, ex, ey, bullets)
            elif self.pattern == 'circular':
                self.shoot_circular(ex, ey, bullets)
            elif self.pattern == 'spiral':
                self.shoot_spiral(ex, ey, bullets)
            else:
                self.shoot_normal(px, py, ex, ey, bullets)
    
    def shoot_normal(self, px, py, ex, ey, bullets):
        angle = math.atan2(py - ey, px - ex)
        bullets.append(EnemyBullet(ex, ey, angle))

    def shoot_n_way(self, px, py, ex, ey, bullets, num_bullets=5, spread_deg=45):
        center_angle = math.atan2(py - ey, px - ex)
        spread_rad = math.radians(spread_deg)
        start_angle = center_angle - spread_rad / 2
        angle_step = spread_rad / (num_bullets - 1) if num_bullets > 1 else 0
        for i in range(num_bullets):
            angle = start_angle + i * angle_step
            bullets.append(EnemyBullet(ex, ey, angle))

    def shoot_circular(self, ex, ey, bullets, num_bullets=16):
        angle_step = 2 * math.pi / num_bullets
        for i in range(num_bullets):
            angle = i * angle_step
            bullets.append(EnemyBullet(ex, ey, angle))

    def shoot_spiral(self, ex, ey, bullets, angle_step_deg=20):
        angle_rad = math.radians(self.spiral_angle)
        bullets.append(EnemyBullet(ex, ey, angle_rad))
        self.spiral_angle = (self.spiral_angle + angle_step_deg) % 360

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, 8) # RED
        # HP Bar
        if self.hp > 0:
            hp_bar_width = self.w * (self.hp / self.max_hp)
            pyxel.rect(self.x, self.y - 4, self.w, 2, 0)
            pyxel.rect(self.x, self.y - 4, hp_bar_width, 2, 11) # GREEN

# --- 弾クラス ---
class PlayerBullet:
    def __init__(self, x, y):
        self.w, self.h = 2, 5
        self.x = x - self.w / 2
        self.y = y
        self.speed_y = -4
        self.damage = 10
        self.is_alive = True

    def update(self):
        self.y += self.speed_y
        if self.y + self.h < 0:
            self.is_alive = False

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, 7) # WHITE

class EnemyBullet:
    def __init__(self, x, y, angle):
        self.r = 3 # 半径
        self.x, self.y = x, y
        speed = 2
        self.speed_x = math.cos(angle) * speed
        self.speed_y = math.sin(angle) * speed
        self.damage = 20
        self.is_alive = True

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        if (self.x + self.r < 0 or self.x - self.r > SCREEN_WIDTH or
            self.y + self.r < 0 or self.y - self.r > SCREEN_HEIGHT):
            self.is_alive = False

    def draw(self):
        pyxel.circ(self.x, self.y, self.r, 13) # PINK

# --- メインのAppクラス ---
class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, fps=60)
        #pyxel.caption("東方風シューティング in Pyxel")
        
        # --- 効果音の作成 ---
        pyxel.sounds[0].set("g1", "n", "4", "f", 20)      # プレイヤー被弾音
        pyxel.sounds[1].set("c3", "t", "5", "n", 8)      # 攻撃ヒット音
        pyxel.sounds[2].set("g2g1c1", "p", "6", "f", 10) # 敵撃破音

        # --- BGM用サウンドの作成 ---
        pyxel.sounds[3].set("c1e1g1c2", "n", "5", "n", 10)      # ドラム
        pyxel.sounds[4].set("c2c2g1g1 a1a1g1g1", "p", "4", "n", 10) # ベース
        pyxel.sounds[5].set("g3d3g3d3 a3d3g3d3", "t", "6", "v", 10) # メロディ
        pyxel.sounds[6].set("c2e2g2c3 g2e2c2g1", "t", "5", "v", 8) # アルペジオ

        # --- 音楽トラックの作成 ---
        pyxel.music(0).set([3, 4], [5], [6], [])
        
        self.scene = SCENE_NAME_INPUT
        self.player_name = ""
        self.input_char_map = self.create_char_map()
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        """ゲームの状態をリセットする"""
        self.player = Player()
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.score = 0
        self.enemy_kill_count = 0
        self.level = 1
        self.time_limit_sec = 20
        self.start_frame = pyxel.frame_count
        self.remaining_time = self.time_limit_sec

    def create_char_map(self):
        """キーコードと文字のマッピングを作成"""
        char_map = {pyxel.KEY_SPACE: " "}
        for i in range(10):
            char_map[pyxel.KEY_0 + i] = str(i)
        for i in range(26):
            char_map[pyxel.KEY_A + i] = chr(ord('A') + i)
        return char_map

    def update(self):
        """全体の更新処理"""
        if pyxel.btnp(pyxel.KEY_Q) and pyxel.btn(pyxel.KEY_LSHIFT):
            pyxel.quit()
        
        if self.scene == SCENE_NAME_INPUT:
            self.update_name_input()
        elif self.scene == SCENE_LEVEL_START:
            self.update_level_start()
        elif self.scene == SCENE_PLAY:
            self.update_play()
        elif self.scene == SCENE_GAMEOVER:
            self.update_gameover()
        elif self.scene == SCENE_GAME_CLEAR:
            self.update_game_clear()

    def draw(self):
        """全体の描画処理"""
        pyxel.cls(0) # 背景を黒でクリア
        if self.scene == SCENE_NAME_INPUT:
            self.draw_name_input()
        elif self.scene == SCENE_LEVEL_START:
            self.draw_level_start()
        elif self.scene == SCENE_PLAY:
            self.draw_play()
        elif self.scene == SCENE_GAMEOVER:
            self.draw_gameover()
        elif self.scene == SCENE_GAME_CLEAR:
            self.draw_game_clear()

    # --- 名前入力シーン ---
    def update_name_input(self):
        if pyxel.btnp(pyxel.KEY_RETURN) and self.player_name:
            self.scene = SCENE_LEVEL_START
            self.level_start_timer = 90
            return
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.player_name = self.player_name[:-1]
        
        if len(self.player_name) < 10:
            for key, char in self.input_char_map.items():
                if pyxel.btnp(key):
                    self.player_name += char

    def draw_name_input(self):
        self.draw_text_centered("ENTER YOUR NAME", 60, 7)
        name_w = len(self.player_name) * pyxel.FONT_WIDTH
        pyxel.text( (SCREEN_WIDTH - name_w) / 2, 110, self.player_name, 7)
        if pyxel.frame_count % 30 < 15:
            pyxel.rect((SCREEN_WIDTH + name_w) / 2, 110, 5, 7, 7)
        self.draw_text_centered("PRESS ENTER TO START", 180, 7)

    # --- レベルスタートシーン ---
    def update_level_start(self):
        self.level_start_timer -= 1
        if self.level_start_timer <= 0:
            if self.level == 5:
                enemy1 = Enemy(pattern_type='circular')
                enemy1.x = SCREEN_WIDTH * 0.25
                enemy2 = Enemy(pattern_type='spiral')
                enemy2.x = SCREEN_WIDTH * 0.75
                self.enemies = [enemy1, enemy2]
            else:
                patterns = ['normal', 'n_way', 'circular', 'spiral']
                pattern_index = (self.level - 1) % len(patterns)
                next_pattern = patterns[pattern_index]
                self.enemies = [Enemy(pattern_type=next_pattern)]
            
            self.scene = SCENE_PLAY
            pyxel.playm(0, loop=True)

    def draw_level_start(self):
        level_text = f"LEVEL {self.level}"
        self.draw_text_centered(level_text, 110, 7)

    # --- ゲームプレイシーン ---
    def update_play(self):
        self.player.update()
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.player_bullets.append(PlayerBullet(self.player.x + self.player.w / 2, self.player.y))

        for enemy in self.enemies:
            enemy.update(self.player, self.enemy_bullets)

        for b in self.player_bullets: b.update()
        for b in self.enemy_bullets: b.update()

        for pb in self.player_bullets:
            for e in self.enemies:
                if (e.is_alive and pb.is_alive and 
                    pb.x < e.x + e.w and pb.x + pb.w > e.x and
                    pb.y < e.y + e.h and pb.y + pb.h > e.y):
                    pb.is_alive = False
                    e.hp -= pb.damage
                    self.score += 100
                    pyxel.play(1, 1)

                    if e.hp <= 0:
                        e.is_alive = False
                        self.score += 1000
                        self.enemy_kill_count += 1
                        pyxel.play(2, 2)

                        is_stage_clear = all(not enemy.is_alive for enemy in self.enemies)
                        if is_stage_clear:
                            pyxel.stop()
                            if self.level == 5:
                                self.score += 10000
                                self.ranking_data = update_ranking(self.player_name, self.score)
                                self.scene = SCENE_GAME_CLEAR
                            else:
                                self.level += 1
                                self.scene = SCENE_LEVEL_START
                                self.level_start_timer = 90
                                self.start_frame += 20 * 60  #追加時間

        for eb in self.enemy_bullets:
            dist = math.sqrt((eb.x - (self.player.x + self.player.w/2))**2 + 
                             (eb.y - (self.player.y + self.player.h/2))**2)
            if eb.is_alive and dist < eb.r + self.player.w/2:
                 eb.is_alive = False
                 self.player.hp -= eb.damage
                 pyxel.play(0, 0)

        self.player_bullets = [b for b in self.player_bullets if b.is_alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.is_alive]

        # 経過時間を計算
        elapsed_sec = (pyxel.frame_count - self.start_frame) / 60
        self.remaining_time = self.time_limit_sec - elapsed_sec
        
        # 時間切れ、またはプレイヤーのHPが0になったらゲームオーバー
        if self.remaining_time <= 0 or self.player.hp <= 0:
            pyxel.stop()
            self.ranking_data = update_ranking(self.player_name, self.score)
            self.scene = SCENE_GAMEOVER

    def draw_play(self):
        self.player.draw()
        for e in self.enemies: e.draw()
        for b in self.player_bullets: b.draw()
        for b in self.enemy_bullets: b.draw()

        s = f"SCORE: {self.score}"
        pyxel.text((SCREEN_WIDTH - len(s) * pyxel.FONT_WIDTH)/2, 5, s, 7)
        
        hp = max(0, self.player.hp)
        pyxel.rect(10, 5, 50, 5, 0)
        pyxel.rect(10, 5, 50 * (hp / self.player.max_hp), 5, 11)
        pyxel.rectb(10, 5, 50, 5, 7)

        t = f"TIME: {int(self.remaining_time)}"
        pyxel.text(SCREEN_WIDTH - len(t) * pyxel.FONT_WIDTH - 5, 5, t, 7)

    # --- ゲームオーバー/ゲームクリア シーン ---
    def update_gameover(self):
        if pyxel.btnp(pyxel.KEY_R):
            pyxel.stop()
            self.reset_game()
            self.scene = SCENE_LEVEL_START
            self.level_start_timer = 90
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw_gameover(self):
        self.draw_text_centered("GAME OVER", 40, 8)
        self.draw_text_centered(f"SCORE: {self.score}", 60, 7)
        self.draw_text_centered("- RANKING -", 90, 10)
        for i, entry in enumerate(self.ranking_data):
            rank_text = f"{i+1}. {entry['name']} - {entry['score']}"
            self.draw_text_centered(rank_text, 110 + i * 10, 7)
        self.draw_text_centered("R: RETRY / Q: QUIT", 200, 7)

    def update_game_clear(self):
        if pyxel.btnp(pyxel.KEY_R):
            pyxel.stop()
            self.reset_game()
            self.scene = SCENE_LEVEL_START
            self.level_start_timer = 90
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw_game_clear(self):
        self.draw_text_centered("GAME CLEAR!", 40, 11)
        self.draw_text_centered(f"SCORE: {self.score}", 60, 7)
        self.draw_text_centered("- RANKING -", 90, 10)
        for i, entry in enumerate(self.ranking_data):
            rank_text = f"{i+1}. {entry['name']} - {entry['score']}"
            self.draw_text_centered(rank_text, 110 + i * 10, 7)
        self.draw_text_centered("R: RETRY / Q: QUIT", 200, 7)
    
    def draw_text_centered(self, text, y, col):
        x = (SCREEN_WIDTH - len(text) * pyxel.FONT_WIDTH) / 2
        pyxel.text(x, y, text, col)

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    App()