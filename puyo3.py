import sys
import random
import math
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect

# TTS機能のインポート
try:
    import pyttsx3
    has_tts = True
except ImportError:
    has_tts = False

# 定数
GRID_WIDTH = 6
GRID_HEIGHT = 12
PUYO_SIZE = 32
BOARD_PADDING = 20

# 色の定義を本物のぷよぷよ通に近づける
BLACK = QColor(0, 0, 0)
WHITE = QColor(255, 255, 255)
RED = QColor(255, 50, 50)       # より鮮やかな赤
GREEN = QColor(20, 200, 20)     # よりぷよぷよらしい緑
BLUE = QColor(50, 80, 255)      # より濃い青
YELLOW = QColor(255, 230, 0)    # より明るい黄色
PURPLE = QColor(200, 0, 200)    # 紫ぷよ用
CYAN = QColor(0, 200, 200)      # 水色ぷよ用
GRID_COLOR = QColor(80, 80, 150) # 紺色のグリッド
BG_COLOR = QColor(0, 0, 60)      # より暗い青背景

# ゲーム版の背景色
BOARD_BG_COLOR = QColor(0, 0, 30)  # さらに暗い青

# ぷよの色（本物のぷよぷよ通に合わせる）
PUYO_COLORS = [RED, GREEN, BLUE, YELLOW]  # 基本の4色

# お邪魔ぷよの色を追加
OJAMA_COLOR = QColor(180, 180, 180)  # お邪魔ぷよは灰色
PUYO_COLORS.append(OJAMA_COLOR)  # 色のリストにお邪魔ぷよを追加

# ぷよの色名
PUYO_COLOR_NAMES = {
    str(RED.getRgb()): "赤",
    str(GREEN.getRgb()): "緑",
    str(BLUE.getRgb()): "青",
    str(YELLOW.getRgb()): "黄",
    str(OJAMA_COLOR.getRgb()): "おじゃま"
}

# 連鎖ボイス
CHAIN_VOICES = {
    2: "ファイヤー",
    3: "アイスストーム",
    4: "ダイアキュート",
    5: "ばよえーん",
    6: "イレブンチェーン",
    7: "マジカルフィーバー",
    8: "ブレインダンプ",
    9: "ジュゲム",
    10: "バイオレットハイ",
    11: "ミラクルボンバー",
    12: "ファンタスティック"
}

# AIの思考時間（秒）
AI_THINKING_TIME = 0.5  # AIがぷよを配置するまでの時間

# お邪魔ぷよの攻撃力計算用の定数
OJAMA_BASE = 10  # 基本攻撃力
CHAIN_BONUS = [0, 0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 480, 512]  # 連鎖ボーナス
COLOR_BONUS = [0, 0, 3, 6, 12, 24]  # 色数ボーナス
GROUP_BONUS = [0, 0, 0, 0, 0, 2, 3, 4, 5, 6, 7, 10]  # 同時消しボーナス

# TTS初期化
if has_tts:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)

# ぷよぷよのクラス
class Puyo:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.falling = True
        self.connected = False
        self.checked = False
        self.visual_y = y  # 表示上の位置
        self.target_y = y  # 目標位置
        self.eyes_open = True  # 目の開閉状態
        self.blink_timer = random.uniform(2.0, 5.0)   # まばたきタイマー
        self.is_ojama = color == OJAMA_COLOR  # お邪魔ぷよかどうか

    def update(self, dt):
        # 視覚的な位置を目標位置に近づける
        if self.visual_y < self.target_y:
            self.visual_y = min(self.target_y, self.visual_y + dt * 10)  # 落下速度を調整
        
        # まばたき処理
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.eyes_open = not self.eyes_open
            # 目を開けている時間は長く、閉じている時間は短く
            if self.eyes_open:
                self.blink_timer = random.uniform(2.0, 5.0)  # 2〜5秒開ける
            else:
                self.blink_timer = random.uniform(0.1, 0.3)  # 0.1〜0.3秒閉じる

    def draw(self, painter, board_x, board_y):
        # 表示上の位置を使って描画
        center_x = int(board_x + self.x * PUYO_SIZE + PUYO_SIZE // 2)
        center_y = int(board_y + self.visual_y * PUYO_SIZE + PUYO_SIZE // 2)
        radius = PUYO_SIZE // 2 - 2
    
        # ぷよの影を描画
        shadow_offset = 2
        shadow_color = QColor(0, 0, 0, 100)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(center_x + shadow_offset, center_y + shadow_offset), radius, radius)
    
        # ぷよの本体を描画
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黒い輪郭線
        painter.drawEllipse(QPoint(center_x, center_y), radius, radius)
        
        # ぷよぷよらしい光沢をつける（楕円形の白いハイライト）
        highlight_size_x = radius * 0.7
        highlight_size_y = radius * 0.5
        highlight_offset_x = -radius * 0.2
        highlight_offset_y = -radius * 0.3
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPoint(center_x + int(highlight_offset_x), center_y + int(highlight_offset_y)),
            int(highlight_size_x), int(highlight_size_y)
        )
        
        # お邪魔ぷよは別の顔を描画
        if self.is_ojama:
            # お邪魔ぷよの目（X型の目）
            eye_spacing = radius * 0.4
            eye_y_pos = int(center_y - radius * 0.1)
            eye_radius = radius * 0.25
            
            # 目の交差する線（X）
            painter.setPen(QPen(BLACK, 2))
            # 左目
            painter.drawLine(
                center_x - int(eye_spacing) - int(eye_radius), eye_y_pos - int(eye_radius),
                center_x - int(eye_spacing) + int(eye_radius), eye_y_pos + int(eye_radius)
            )
            painter.drawLine(
                center_x - int(eye_spacing) - int(eye_radius), eye_y_pos + int(eye_radius),
                center_x - int(eye_spacing) + int(eye_radius), eye_y_pos - int(eye_radius)
            )
            # 右目
            painter.drawLine(
                center_x + int(eye_spacing) - int(eye_radius), eye_y_pos - int(eye_radius),
                center_x + int(eye_spacing) + int(eye_radius), eye_y_pos + int(eye_radius)
            )
            painter.drawLine(
                center_x + int(eye_spacing) - int(eye_radius), eye_y_pos + int(eye_radius),
                center_x + int(eye_spacing) + int(eye_radius), eye_y_pos - int(eye_radius)
            )
            
            # 口（直線）
            mouth_y = int(center_y + radius * 0.3)
            painter.drawLine(
                center_x - int(radius * 0.4), mouth_y,
                center_x + int(radius * 0.4), mouth_y
            )
        else:
            # 通常のぷよの目
            eye_spacing = radius * 0.4
            eye_y_pos = int(center_y - radius * 0.1)
            eye_radius = radius * 0.25
            
            # 白目
            painter.setBrush(QBrush(WHITE))
            painter.setPen(QPen(BLACK, 1))
            painter.drawEllipse(QPoint(center_x - int(eye_spacing), eye_y_pos), int(eye_radius), int(eye_radius))
            painter.drawEllipse(QPoint(center_x + int(eye_spacing), eye_y_pos), int(eye_radius), int(eye_radius))
            
            # 瞳（黒目）- まばたきしていない時だけ
            if self.eyes_open:
                pupil_radius = eye_radius * 0.6
                painter.setBrush(QBrush(BLACK))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(center_x - int(eye_spacing), eye_y_pos), int(pupil_radius), int(pupil_radius))
                painter.drawEllipse(QPoint(center_x + int(eye_spacing), eye_y_pos), int(pupil_radius), int(pupil_radius))
            else:
                # 閉じた目（線）
                painter.setPen(QPen(BLACK, 2))
                painter.drawLine(
                    center_x - int(eye_spacing) - int(eye_radius), eye_y_pos,
                    center_x - int(eye_spacing) + int(eye_radius), eye_y_pos
                )
                painter.drawLine(
                    center_x + int(eye_spacing) - int(eye_radius), eye_y_pos,
                    center_x + int(eye_spacing) + int(eye_radius), eye_y_pos
                )

# ぷよぷよのペアクラス
class PuyoPair:
    def __init__(self, x, grid, available_colors=None):
        self.x = x
        self.y = 0
        self.rotation = 0  # 0: 上, 1: 右, 2: 下, 3: 左
        self.grid = grid
        
        # 使用可能な色が指定されていない場合、デフォルトの色を使用
        if available_colors is None:
            # お邪魔ぷよは通常のペアには含めない
            available_colors = [color for color in PUYO_COLORS if color != OJAMA_COLOR]
        
        self.colors = [random.choice(available_colors), random.choice(available_colors)]
        self.puyo1 = Puyo(x, 0, self.colors[0])
        self.puyo2 = Puyo(x, 1, self.colors[1])
        
        # 初期状態では視覚的な位置を論理位置より上に設定（上から落ちてくる演出）
        self.puyo1.visual_y = -1
        self.puyo2.visual_y = 0
        self.puyo1.target_y = 0
        self.puyo2.target_y = 1
    
    def rotate(self, direction):
        # 1: 時計回り, -1: 反時計回り
        old_rotation = self.rotation
        self.rotation = (self.rotation + direction) % 4
        
        # 回転後の位置をチェック
        if not self.can_rotate():
            # 回転できなければ元に戻す
            self.rotation = old_rotation
            return False
            
        self.update_positions()
        
        # 回転後に視覚的な位置も即座に更新
        self.puyo1.visual_y = self.puyo1.y
        self.puyo2.visual_y = self.puyo2.y
        
        return True
    
    def can_rotate(self):
        # 回転先の位置をチェック
        rot = self.rotation
        new_x1, new_y1 = self.x, self.y
        
        if rot == 0:  # 上
            new_x2, new_y2 = self.x, self.y + 1
        elif rot == 1:  # 右
            new_x2, new_y2 = self.x + 1, self.y
        elif rot == 2:  # 下
            new_x2, new_y2 = self.x, self.y + 1
        elif rot == 3:  # 左
            new_x2, new_y2 = self.x - 1, self.y
            
        # グリッド内にあるか
        if (new_x1 < 0 or new_x1 >= GRID_WIDTH or new_y1 < 0 or new_y1 >= GRID_HEIGHT or
            new_x2 < 0 or new_x2 >= GRID_WIDTH or new_y2 < 0 or new_y2 >= GRID_HEIGHT):
            return False
            
        # 他のぷよと重ならないか
        if (self.grid[new_y1][new_x1] is not None or self.grid[new_y2][new_x2] is not None):
            return False
            
        return True
    
    def update_positions(self):
        if self.rotation == 0:  # 上
            self.puyo1.x = self.x
            self.puyo1.y = self.y
            self.puyo2.x = self.x
            self.puyo2.y = self.y + 1
        elif self.rotation == 1:  # 右
            self.puyo1.x = self.x
            self.puyo1.y = self.y
            self.puyo2.x = self.x + 1
            self.puyo2.y = self.y
        elif self.rotation == 2:  # 下
            self.puyo1.x = self.x
            self.puyo1.y = self.y + 1
            self.puyo2.x = self.x
            self.puyo2.y = self.y
        elif self.rotation == 3:  # 左
            self.puyo1.x = self.x
            self.puyo1.y = self.y
            self.puyo2.x = self.x - 1
            self.puyo2.y = self.y
        
        # ターゲット位置も更新
        self.puyo1.target_y = self.puyo1.y
        self.puyo2.target_y = self.puyo2.y
    
    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 移動先がグリッド内にあるか確認
        if self.can_move(new_x, new_y):
            self.x = new_x
            self.y = new_y
            
            # 視覚的な位置も更新
            if dy > 0:  # 下に移動する場合
                self.puyo1.target_y = self.puyo1.y
                self.puyo2.target_y = self.puyo2.y
            else:  # それ以外の移動の場合は即座に視覚的位置も更新
                self.puyo1.visual_y = self.puyo1.y
                self.puyo2.visual_y = self.puyo2.y
                
            self.update_positions()
            return True
        return False
        
    def drop_to_bottom(self):
        # 一番下まで落とす（ちぎり機能）
        while self.move(0, 1):
            pass
    
    def can_move(self, new_x, new_y):
        rot = self.rotation
        # 上
        if rot == 0:
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y + 1 >= GRID_HEIGHT:
                return False
            if self.grid[new_y][new_x] is not None or self.grid[new_y + 1][new_x] is not None:
                return False
        # 右
        elif rot == 1:
            if new_x < 0 or new_x + 1 >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                return False
            if self.grid[new_y][new_x] is not None or self.grid[new_y][new_x + 1] is not None:
                return False
        # 下
        elif rot == 2:
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y + 1 >= GRID_HEIGHT:
                return False
            if self.grid[new_y][new_x] is not None or self.grid[new_y + 1][new_x] is not None:
                return False
        # 左
        elif rot == 3:
            if new_x - 1 < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                return False
            if self.grid[new_y][new_x] is not None or self.grid[new_y][new_x - 1] is not None:
                return False
        return True

    def update(self, dt):
        # ぷよの視覚的な位置を更新
        self.puyo1.update(dt)
        self.puyo2.update(dt)

    def draw(self, painter, board_x, board_y):
        # 両方のぷよを描画
        self.puyo1.draw(painter, board_x, board_y)
        self.puyo2.draw(painter, board_x, board_y)

# AIプレイヤークラス
class AIPlayer:
    def __init__(self, game_logic):
        self.game_logic = game_logic
        self.thinking_time = 0
        self.move_delay = 0
        self.rotation_delay = 0
        self.decided_moves = []  # AIの次の動きのリスト [(移動方向, 回転方向)]
        self.current_move_index = 0
        self.drop_ready = False  # ぷよを落とす準備ができたか
    
    def reset(self):
        self.thinking_time = 0
        self.decided_moves = []
        self.current_move_index = 0
        self.drop_ready = False
        self.move_delay = 0
        self.rotation_delay = 0
    
    def update(self, dt):
        if self.game_logic.game_over or self.game_logic.falling_puyos or self.game_logic.waiting_for_pop or self.game_logic.fall_animation_in_progress:
            return
        
        # 思考時間を更新
        if len(self.decided_moves) == 0:
            self.thinking_time += dt
            if self.thinking_time >= AI_THINKING_TIME:
                self.thinking_time = 0
                self.decide_next_move()
        
        # 移動とローテーションの遅延を処理
        if self.move_delay > 0:
            self.move_delay -= dt
            return
        
        if self.rotation_delay > 0:
            self.rotation_delay -= dt
            return
        
        # 決定した動きを実行
        if len(self.decided_moves) > 0 and self.current_move_index < len(self.decided_moves):
            move = self.decided_moves[self.current_move_index]
            
            if move[0] != 0:  # 横移動
                self.game_logic.current_pair.move(move[0], 0)
                self.move_delay = 0.1  # 横移動の遅延
            elif move[1] != 0:  # 回転
                self.game_logic.current_pair.rotate(move[1])
                self.rotation_delay = 0.15  # 回転の遅延
            
            self.current_move_index += 1
        
        # すべての動きが完了した場合、ぷよを落とす
        elif len(self.decided_moves) > 0 and self.current_move_index >= len(self.decided_moves) and not self.drop_ready:
            self.drop_ready = True
            self.game_logic.quick_drop()  # ぷよを落とす
            self.decided_moves = []  # 動きをリセット
            self.current_move_index = 0
            self.drop_ready = False
    
    def decide_next_move(self):
        """次の最適な動きを決定する"""
        best_score = -1
        best_moves = []
        
        # 現在のぷよペアの色を取得
        color1 = self.game_logic.current_pair.colors[0]
        color2 = self.game_logic.current_pair.colors[1]
        
        # 各列と回転の組み合わせをシミュレーション
        for column in range(GRID_WIDTH):
            for rotation in range(4):  # 0: 上, 1: 右, 2: 下, 3: 左
                # 必要な移動と回転を計算
                moves = self.calculate_moves(column, rotation)
                if moves is None:  # 無効な位置の場合
                    continue
                
                # 仮想的にぷよを配置してスコアを計算
                score = self.evaluate_placement(column, rotation, color1, color2)
                
                if score > best_score:
                    best_score = score
                    best_moves = moves
        
        # 最適な動きがなかった場合、ランダムな動きを選択
        if not best_moves:
            # 左右のランダムな移動
            rand_column = random.randint(0, GRID_WIDTH-1)
            rand_rotation = random.randint(0, 3)
            best_moves = self.calculate_moves(rand_column, rand_rotation) or []
        
        self.decided_moves = best_moves
    
    def calculate_moves(self, target_column, target_rotation):
        """目標の列と回転に到達するために必要な移動とローテーションを計算"""
        moves = []
        
        # 現在の状態を取得
        current_x = self.game_logic.current_pair.x
        current_rotation = self.game_logic.current_pair.rotation
        
        # 横方向の移動
        dx = target_column - current_x
        
        # 列方向の移動を追加
        for _ in range(abs(dx)):
            moves.append((1 if dx > 0 else -1, 0))
        
        # 回転方向の移動を追加（時計回りまたは反時計回りのうち近い方）
        rotation_diff = (target_rotation - current_rotation) % 4
        if rotation_diff <= 2:
            for _ in range(rotation_diff):
                moves.append((0, 1))  # 時計回り
        else:
            for _ in range(4 - rotation_diff):
                moves.append((0, -1))  # 反時計回り
        
        # 移動後の位置が有効かチェック
        temp_pair = PuyoPair(current_x, self.game_logic.grid)
        temp_pair.rotation = current_rotation
        
        for move in moves:
            if move[0] != 0:  # 横移動
                if not temp_pair.move(move[0], 0):
                    return None  # 無効な移動
            elif move[1] != 0:  # 回転
                if not temp_pair.rotate(move[1]):
                    return None  # 無効な回転
        
        return moves
    
    def evaluate_placement(self, column, rotation, color1, color2):
        """配置の評価関数"""
        # 仮想グリッドを作成
        virtual_grid = [[self.game_logic.grid[y][x] for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]
        
        # ぷよの位置を計算
        x1, y1, x2, y2 = self.calculate_puyo_positions(column, rotation)
        
        if not self.is_valid_position(x1, y1, virtual_grid) or not self.is_valid_position(x2, y2, virtual_grid):
            return -1
        
        # 落下位置を計算
        while y1 + 1 < GRID_HEIGHT and virtual_grid[y1 + 1][x1] is None:
            y1 += 1
        
        while y2 + 1 < GRID_HEIGHT and virtual_grid[y2 + 1][x2] is None:
            y2 += 1
        
        # 仮想的にぷよを配置
        virtual_puyo1 = Puyo(x1, y1, color1)
        virtual_puyo2 = Puyo(x2, y2, color2)
        
        virtual_grid[y1][x1] = virtual_puyo1
        virtual_grid[y2][x2] = virtual_puyo2
        
        # 評価スコア
        score = 0
        
        # 周囲の同色ぷよの数をカウント
        score += self.count_same_color_neighbors(x1, y1, color1, virtual_grid) * 10
        score += self.count_same_color_neighbors(x2, y2, color2, virtual_grid) * 10
        
        # 高さに対するペナルティ（低いほど良い）
        height_penalty = (GRID_HEIGHT - y1) + (GRID_HEIGHT - y2)
        score -= height_penalty * 2
        
        # 中央配置のボーナス
        center_bonus = GRID_WIDTH / 2
        score += (center_bonus - abs(x1 - center_bonus)) + (center_bonus - abs(x2 - center_bonus))
        
        return score
    
    def is_valid_position(self, x, y, grid):
        """座標が有効かチェック"""
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        if grid[y][x] is not None:
            return False
        return True
    
    def calculate_puyo_positions(self, column, rotation):
        """回転に基づいてぷよの位置を計算"""
        x1 = column
        y1 = 0
        
        if rotation == 0:  # 上
            x2, y2 = x1, y1 + 1
        elif rotation == 1:  # 右
            x2, y2 = x1 + 1, y1
        elif rotation == 2:  # 下
            x2, y2 = x1, y1 + 1
        else:  # 左
            x2, y2 = x1 - 1, y1
        
        return x1, y1, x2, y2
    
    def count_same_color_neighbors(self, x, y, color, grid):
        """同じ色の隣接ぷよをカウント"""
        count = 0
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and grid[ny][nx] is not None:
                if grid[ny][nx].color == color:
                    count += 1
        
        return count

# ゲームロジッククラス
class PuyoGameLogic:
    def __init__(self, is_player2=False, opponent=None):
        self.is_player2 = is_player2  # プレイヤー2（AI）かどうか
        self.opponent = opponent  # 対戦相手のゲームロジック
        self.pending_ojama = 0  # 待機中のお邪魔ぷよ数
        self.ojama_drop_timer = 0  # お邪魔ぷよを落とすまでのタイマー
        self.reset()
    
    def reset(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_pair = self.create_new_pair()
        self.next_pair = self.create_new_pair()
        self.fall_time = 0
        self.fall_speed = 0.5  # ぷよが1マス落ちる時間（秒）
        self.game_over = False
        self.score = 0
        self.chain_count = 0
        self.falling_puyos = False
        self.last_key_time = 0
        self.key_delay = 0.15  # キー入力の遅延（秒）
        self.last_rotation_time = 0
        self.rotation_delay = 0.25  # 回転の遅延（秒）
        self.pop_effects = []  # 消去エフェクト（星など）
        self.effect_duration = 1.5  # エフェクトの持続時間を1.5秒に延長
        self.puyo_pop_state = {}  # ぷよの消去状態を管理
        self.flash_frequency = 8  # 点滅の頻度（1秒あたりの回数）
        self.waiting_for_pop = False  # 消去アニメーション待機中
        self.pop_wait_time = 0.0  # 待機時間
        self.pop_wait_duration = 1.0  # 消去後の待機時間（秒）
        self.fall_animation_in_progress = False  # 落下アニメーション中
        self.pending_ojama = 0  # 待機中のお邪魔ぷよ数をリセット
        self.ojama_drop_timer = 0  # お邪魔ぷよを落とすまでのタイマーをリセット
    
    def create_new_pair(self):
        # お邪魔ぷよは通常ぷよペアとして生成されない
        available_colors = [color for color in PUYO_COLORS if color != OJAMA_COLOR]
        return PuyoPair(GRID_WIDTH // 2 - 1, self.grid, available_colors)
    
    def add_puyos_to_grid(self, puyo1, puyo2):
        if 0 <= puyo1.y < GRID_HEIGHT and 0 <= puyo1.x < GRID_WIDTH:
            self.grid[puyo1.y][puyo1.x] = puyo1
            puyo1.target_y = puyo1.y
        if 0 <= puyo2.y < GRID_HEIGHT and 0 <= puyo2.x < GRID_WIDTH:
            self.grid[puyo2.y][puyo2.x] = puyo2
            puyo2.target_y = puyo2.y
                
        # 横に置いた場合、下が空いていれば落とす処理
        self.handle_floating_puyos()
    
    def handle_floating_puyos(self):
        # 横に置いて空中に浮いている状態のぷよを落とす
        puyo_dropped = True
        
        while puyo_dropped:
            puyo_dropped = False
            for y in range(GRID_HEIGHT - 2, -1, -1):
                for x in range(GRID_WIDTH):
                    if self.grid[y][x] is not None and self.grid[y + 1][x] is None:
                        # 下が空いている場合は落とす
                        self.grid[y + 1][x] = self.grid[y][x]
                        self.grid[y + 1][x].y = y + 1
                        self.grid[y + 1][x].target_y = y + 1  # 目標位置を更新
                        self.grid[y][x] = None
                        puyo_dropped = True
                        self.fall_animation_in_progress = True  # アニメーション中フラグをセット
    
    def check_game_over(self):
        # 上部の行に固定されたぷよがあるかチェック
        if self.grid[1][GRID_WIDTH // 2 - 1] is not None or self.grid[1][GRID_WIDTH // 2] is not None:
            self.game_over = True
            
    def quick_drop(self):
        # ちぎり機能（一番下まで落とす）
        if not self.falling_puyos and not self.game_over and not self.fall_animation_in_progress:
            self.current_pair.drop_to_bottom()
                
            # 落下アニメーションのための視覚的位置の更新
            self.current_pair.puyo1.target_y = self.current_pair.puyo1.y
            self.current_pair.puyo2.target_y = self.current_pair.puyo2.y
            self.fall_animation_in_progress = True
                
            # 固定する
            self.add_puyos_to_grid(self.current_pair.puyo1, self.current_pair.puyo2)
            # 連鎖チェック
            if not self.check_matches():
                self.current_pair = self.next_pair
                self.next_pair = self.create_new_pair()
                self.check_game_over()
    
    def drop_ojama_puyos(self):
        """お邪魔ぷよを落とす処理"""
        if self.pending_ojama <= 0:
            return
        
        # 落とす数（最大で一度に30個まで）
        drop_count = min(self.pending_ojama, 30)
        self.pending_ojama -= drop_count
        
        # 各列にランダムに配置
        columns = list(range(GRID_WIDTH))
        random.shuffle(columns)
        
        for i in range(drop_count):
            col = columns[i % GRID_WIDTH]
            
            # 列の一番上が空いているか確認
            if self.grid[0][col] is not None:
                continue
            
            # 落下位置を計算
            row = 0
            while row + 1 < GRID_HEIGHT and self.grid[row + 1][col] is None:
                row += 1
            
            # お邪魔ぷよを作成して配置
            ojama_puyo = Puyo(col, row, OJAMA_COLOR)
            ojama_puyo.is_ojama = True  # お邪魔ぷよフラグをセット
            self.grid[row][col] = ojama_puyo
            
            # 視覚的な位置設定（上から落ちてくる）
            ojama_puyo.visual_y = -1
            ojama_puyo.target_y = row
            
            self.fall_animation_in_progress = True
    
    def check_matches(self):
        # 全てのぷよのcheckedフラグをリセット
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] is not None:
                    self.grid[y][x].checked = False
        
        groups = []
        color_groups = {}  # 色ごとのグループ
        
        # 4つ以上連結したぷよを探す
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] is not None and not self.grid[y][x].checked:
                    # お邪魔ぷよは通常の連鎖に含めない
                    if hasattr(self.grid[y][x], 'is_ojama') and self.grid[y][x].is_ojama:
                        continue
                    
                    current_color = self.grid[y][x].color
                    group = self.find_connected_puyos(x, y, current_color)
                    
                    if len(group) >= 4:
                        groups.append(group)
                        
                        # 色ごとのグループを記録
                        color_key = str(current_color.getRgb())
                        if color_key not in color_groups:
                            color_groups[color_key] = []
                        color_groups[color_key].append(group)
        
        # 連鎖があればぷよを消して得点計算
        if groups:
            self.chain_count += 1
            total_cleared = 0
            
            # 連鎖ボイスの再生
            if self.chain_count in CHAIN_VOICES and has_tts:
                self.play_chain_voice(self.chain_count)
            
            # ぷよを消す&エフェクトを追加
            for group in groups:
                total_cleared += len(group)
                for puyo in group:
                    # ぷよの消去状態を作成
                    puyo_key = f"{puyo.x},{puyo.y}"
                    self.puyo_pop_state[puyo_key] = {
                        "x": puyo.x,
                        "y": puyo.y,
                        "color": puyo.color,
                        "time": self.effect_duration,
                        "scale": 1.0,
                        "chain": self.chain_count,
                        "original_puyo": puyo,
                        "brightness": 0.0,
                        "phase": 0.0
                    }
                    
                    # 連鎖数に応じた星エフェクト
                    if self.chain_count > 1:
                        star_count = min(1 + (self.chain_count - 1) // 2, 5)
                        
                        for i in range(star_count):
                            angle = (i * 360 / star_count) * 3.14159 / 180
                            offset_x = math.cos(angle) * 0.5
                            offset_y = math.sin(angle) * 0.5
                            
                            self.pop_effects.append({
                                "x": puyo.x + offset_x,
                                "y": puyo.y + offset_y,
                                "color": puyo.color,
                                "time": self.effect_duration,
                                "radius": PUYO_SIZE // 2,
                                "chain": self.chain_count,
                                "type": "star"
                            })
                    
                    # グリッドから削除
                    self.grid[puyo.y][puyo.x] = None
            
            # 隣接するお邪魔ぷよも消す
            self.clear_adjacent_ojama_puyos()
            
            # 得点計算
            chain_power = self.calculate_chain_power()
            group_bonus = self.calculate_group_bonus(len(groups))
            color_bonus = self.calculate_color_bonus(len(color_groups))
            
            power = max(1, chain_power + group_bonus + color_bonus)
            score_formula = 10 * total_cleared * power
            self.score += score_formula
            
            # お邪魔ぷよの攻撃力計算
            ojama_count = self.calculate_ojama_attack(total_cleared, power)
            
            # 対戦相手にお邪魔ぷよを送る
            if self.opponent is not None:
                self.opponent.pending_ojama += ojama_count
            
            # 消去アニメーション待機状態に移行
            self.waiting_for_pop = True
            self.pop_wait_time = 0.0
            
            return True
        else:
            self.chain_count = 0
            return False
    
    def clear_adjacent_ojama_puyos(self):
        """消去されたぷよに隣接するお邪魔ぷよを消去"""
        ojama_to_clear = []
        
        # 消去されたぷよの位置を取得
        cleared_positions = []
        for key in self.puyo_pop_state:
            x, y = map(int, key.split(','))
            cleared_positions.append((x, y))
        
        # 隣接するお邪魔ぷよを探す
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for x, y in cleared_positions:
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and self.grid[ny][nx] is not None:
                    puyo = self.grid[ny][nx]
                    if hasattr(puyo, 'is_ojama') and puyo.is_ojama:
                        ojama_to_clear.append((nx, ny, puyo))
        
        # お邪魔ぷよを消去
        for x, y, puyo in ojama_to_clear:
            puyo_key = f"{x},{y}"
            if puyo_key not in self.puyo_pop_state:  # まだ消去されていない場合
                self.puyo_pop_state[puyo_key] = {
                    "x": x,
                    "y": y,
                    "color": OJAMA_COLOR,
                    "time": self.effect_duration,
                    "scale": 1.0,
                    "chain": self.chain_count,
                    "original_puyo": puyo,
                    "brightness": 0.0,
                    "phase": 0.0
                }
                self.grid[y][x] = None
    
    def find_connected_puyos(self, x, y, color):
        if (y < 0 or y >= GRID_HEIGHT or x < 0 or x >= GRID_WIDTH or 
                self.grid[y][x] is None or self.grid[y][x].checked or 
                self.grid[y][x].color != color):
            return []
        
        self.grid[y][x].checked = True
        result = [self.grid[y][x]]
        
        # 上下左右を確認
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dx, dy in directions:
            result.extend(self.find_connected_puyos(x + dx, y + dy, color))
        
        return result
    
    def calculate_chain_power(self):
        """連鎖による攻撃力ボーナス"""
        if self.chain_count >= len(CHAIN_BONUS):
            return CHAIN_BONUS[-1]
        return CHAIN_BONUS[self.chain_count]
    
    def calculate_group_bonus(self, group_count):
        """同時消し数による攻撃力ボーナス"""
        if group_count >= len(GROUP_BONUS):
            return GROUP_BONUS[-1]
        return GROUP_BONUS[group_count]
    
    def calculate_color_bonus(self, color_count):
        """色数による攻撃力ボーナス"""
        if color_count >= len(COLOR_BONUS):
            return COLOR_BONUS[-1]
        return COLOR_BONUS[color_count]
    
    def calculate_ojama_attack(self, cleared_count, power):
            """攻撃力からお邪魔ぷよの数を計算"""
            return (cleared_count * power) // OJAMA_BASE
    
    def fall_puyos(self):
        # 論理的な落下処理
        moved = False
        for y in range(GRID_HEIGHT - 2, -1, -1):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] is not None and self.grid[y + 1][x] is None:
                    # 論理的な位置を更新
                    self.grid[y + 1][x] = self.grid[y][x]
                    self.grid[y + 1][x].y = y + 1
                    self.grid[y + 1][x].target_y = y + 1  # 目標位置を設定
                    self.grid[y][x] = None
                    moved = True
                    self.fall_animation_in_progress = True  # アニメーション中フラグをセット
        
        return moved
    
    def play_chain_voice(self, chain_count):
        if chain_count in CHAIN_VOICES and has_tts:
            voice = CHAIN_VOICES[chain_count]
            tts_engine.say(voice)
            tts_engine.runAndWait()
    
    def handle_key_press(self, key):
        if self.falling_puyos or self.game_over or self.waiting_for_pop or self.fall_animation_in_progress:
            return
        
        # キー入力の制限時間を設ける
        import time
        current_time = time.time()
        if current_time - self.last_key_time < self.key_delay:
            return
        
        # 回転に時間がかかるようにする
        if current_time - self.last_rotation_time < self.rotation_delay and (key == Qt.Key_Up or key == Qt.Key_Z or key == Qt.Key_X):
            return
                
        moved = False
        if key == Qt.Key_Left:
            moved = self.current_pair.move(-1, 0)
        elif key == Qt.Key_Right:
            moved = self.current_pair.move(1, 0)
        elif key == Qt.Key_Down:
            moved = self.current_pair.move(0, 1)
        elif key == Qt.Key_Up:  # 上キーに変更
            moved = self.current_pair.rotate(1)  # 回転
            if moved:
                self.last_rotation_time = current_time
        elif key == Qt.Key_Z:
            moved = self.current_pair.rotate(-1)  # 反時計回り
            if moved:
                self.last_rotation_time = current_time
        elif key == Qt.Key_X:
            moved = self.current_pair.rotate(1)   # 時計回り
            if moved:
                self.last_rotation_time = current_time
        elif key == Qt.Key_C:  # Cキーでちぎり（強制落下）
            self.quick_drop()
            moved = True
        elif key == Qt.Key_R and self.game_over:  # ゲームオーバー時のリスタート
            self.reset()
            moved = True
                
        if moved:
            self.last_key_time = current_time
    
    def update_animations(self, dt):
        # ぷよの消去アニメーション更新
        for key, pop_state in list(self.puyo_pop_state.items()):
            pop_state["time"] -= dt
            
            # 全体の進行度（0.0〜1.0）
            progress = 1.0 - (pop_state["time"] / self.effect_duration)
            pop_state["phase"] = progress
            
            # 点滅のためのフラッシュ状態計算（sin波を使用）
            flash_state = math.sin(progress * self.flash_frequency * math.pi * 2) * 0.5 + 0.5
            
            # 消去アニメーションのフェーズで挙動変更 - 連鎖数に関わらず同じ演出
            if progress < 0.2:  # 最初の20%で膨らむ
                pop_state["scale"] = 1.0 + (progress / 0.2) * 0.3  # 最大1.3倍まで膨らむ
                # 点滅しながら明るくなる
                pop_state["brightness"] = progress / 0.2 * 0.4 * (0.5 + flash_state * 0.5)
            elif progress < 0.6:  # 20%〜60%は点滅しながら維持
                pop_state["scale"] = 1.3 - ((progress - 0.2) / 0.4) * 0.1  # わずかに縮む
                # 点滅する明るさ（0.4〜0.7）
                pop_state["brightness"] = 0.4 + flash_state * 0.3
            elif progress < 0.8:  # 60%〜80%は輝きながらゆっくり縮む
                pop_state["scale"] = 1.2 - ((progress - 0.6) / 0.2) * 0.4  # 1.2倍から0.8倍に
                # 完全に明るく（0.7〜1.0）
                pop_state["brightness"] = 0.7 + (progress - 0.6) / 0.2 * 0.3
            else:  # 残り20%で一気に縮んでいく
                pop_state["scale"] = 0.8 - ((progress - 0.8) / 0.2) * 0.8  # 0.8倍から0倍に縮む
                # 最大明るさで消えていく
                pop_state["brightness"] = 1.0
            
            if pop_state["time"] <= 0:
                del self.puyo_pop_state[key]
        
        # エフェクトの更新
        for effect in self.pop_effects[:]:
            effect["time"] -= dt
            if effect["time"] <= 0:
                self.pop_effects.remove(effect)
        
        # 全てのぷよの視覚的な位置を更新
        all_puyos_at_target = True
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] is not None:
                    self.grid[y][x].update(dt)
                    if self.grid[y][x].visual_y < self.grid[y][x].target_y:
                        all_puyos_at_target = False
        
        # 落下アニメーションの終了判定
        if self.fall_animation_in_progress and all_puyos_at_target:
            self.fall_animation_in_progress = False
    
    def update(self, dt):
        if self.game_over:
            return
        
        # アニメーションの更新
        self.update_animations(dt)
        
        # お邪魔ぷよの処理
        if self.pending_ojama > 0 and not self.falling_puyos and not self.waiting_for_pop and not self.fall_animation_in_progress:
            self.ojama_drop_timer += dt
            if self.ojama_drop_timer >= 0.5:  # 0.5秒ごとにお邪魔ぷよを落とす
                self.ojama_drop_timer = 0
                self.drop_ojama_puyos()
        
        # 消去アニメーション待機処理
        if self.waiting_for_pop:
            self.pop_wait_time += dt
            if self.pop_wait_time >= self.pop_wait_duration:
                self.waiting_for_pop = False
                self.pop_wait_time = 0
                self.falling_puyos = True
            return
        
        # 落下アニメーション中は他の操作を止める
        if self.fall_animation_in_progress:
            return
        
        # 通常の落下処理
        if self.falling_puyos:
            if not self.fall_puyos():
                self.falling_puyos = False
                # 落下が終わったら再度連鎖をチェック
                if not self.check_matches():
                    # 連鎖がなければ新しいぷよペアを生成
                    self.current_pair = self.next_pair
                    self.next_pair = self.create_new_pair()
                    self.check_game_over()
            return
        
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if not self.current_pair.move(0, 1):
                # 移動できなければ固定する
                self.add_puyos_to_grid(self.current_pair.puyo1, self.current_pair.puyo2)
                # 連鎖チェック
                if not self.check_matches():
                    self.current_pair = self.next_pair
                    self.next_pair = self.create_new_pair()
                    self.check_game_over()

# 対戦用の新しいゲームウィジェット
class PuyoVsGameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # プレイヤー1とプレイヤー2（AI）のゲームロジックを作成
        self.game_logic_p1 = PuyoGameLogic(is_player2=False)
        self.game_logic_p2 = PuyoGameLogic(is_player2=True)
        
        # お互いを対戦相手として設定
        self.game_logic_p1.opponent = self.game_logic_p2
        self.game_logic_p2.opponent = self.game_logic_p1
        
        # AIプレイヤーの作成
        self.ai_player = AIPlayer(self.game_logic_p2)
        
        # タイマー設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # 約60FPS
        self.last_time = 0
        self.setFocusPolicy(Qt.StrongFocus)  # キー入力を受け付けるようにする
        
        # ウィンドウサイズの設定
        board_width = GRID_WIDTH * PUYO_SIZE + BOARD_PADDING * 2
        board_height = GRID_HEIGHT * PUYO_SIZE + BOARD_PADDING * 2
        
        # プレイヤー1の盤面座標
        self.board_p1_x = BOARD_PADDING
        self.board_p1_y = BOARD_PADDING
        
        # プレイヤー2の盤面座標（右側に配置）
        self.board_p2_x = BOARD_PADDING * 8 + board_width
        self.board_p2_y = BOARD_PADDING
        
        # サイドパネルのサイズ
        side_panel_width = 150
        
        # ウィンドウサイズを設定（2プレーヤー分の幅）
        total_width = board_width * 2 + side_panel_width * 2 + BOARD_PADDING * 4
        self.setMinimumSize(total_width, board_height)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景を描画
        painter.fillRect(self.rect(), BG_COLOR)
        
        # プレイヤー1とプレイヤー2の盤面を描画
        self.draw_game_board(painter, self.game_logic_p1, self.board_p1_x, self.board_p1_y, "PLAYER")
        self.draw_game_board(painter, self.game_logic_p2, self.board_p2_x, self.board_p2_y, "CPU")
        
        # 対戦情報パネルを描画（中央）
        self.draw_vs_panel(painter)
    
    def draw_game_board(self, painter, game_logic, board_x, board_y, player_name):
        # ゲーム盤の背景
        board_rect = QRect(board_x, board_y, GRID_WIDTH * PUYO_SIZE, GRID_HEIGHT * PUYO_SIZE)
        painter.fillRect(board_rect, BOARD_BG_COLOR)
        
        # プレイヤー名を表示
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.drawText(board_x, board_y - 10, player_name)
        
        # グリッドの描画
        painter.setPen(QPen(GRID_COLOR, 1, Qt.DotLine))
        
        for x in range(GRID_WIDTH + 1):
            painter.drawLine(
                board_x + x * PUYO_SIZE, board_y,
                board_x + x * PUYO_SIZE, board_y + GRID_HEIGHT * PUYO_SIZE
            )
        
        for y in range(GRID_HEIGHT + 1):
            painter.drawLine(
                board_x, board_y + y * PUYO_SIZE,
                board_x + GRID_WIDTH * PUYO_SIZE, board_y + y * PUYO_SIZE
            )
        
        # 盤の枠線
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(board_rect)
        
        # グリッド上のぷよを描画
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if game_logic.grid[y][x] is not None:
                    game_logic.grid[y][x].draw(painter, board_x, board_y)
        
        # 消去中のぷよを描画
        self.draw_popping_puyos(painter, game_logic, board_x, board_y)
        
        # 星形エフェクトを描画
        self.draw_star_effects(painter, game_logic, board_x, board_y)
        
        # 現在のぷよペアを描画
        if not game_logic.falling_puyos and not game_logic.game_over and not game_logic.waiting_for_pop:
            game_logic.current_pair.draw(painter, board_x, board_y)
        
        # 次のぷよペアの表示 - 装飾枠追加
        next_panel_x = board_x + GRID_WIDTH * PUYO_SIZE + 20
        next_panel_y = board_y + 20
        next_panel_width = 100
        next_panel_height = 120
        
        # 「NEXT」パネル背景
        next_panel_rect = QRect(next_panel_x, next_panel_y, next_panel_width, next_panel_height)
        painter.fillRect(next_panel_rect, QColor(30, 30, 80))
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(next_panel_rect)
        
        # NEXTラベル
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(next_panel_x + 10, next_panel_y + 25, "NEXT")
        
        # 次のぷよを描画
        next_puyo1_x = next_panel_x + next_panel_width // 2
        next_puyo1_y = next_panel_y + 50
        next_puyo2_x = next_panel_x + next_panel_width // 2
        next_puyo2_y = next_panel_y + 90
        
        # 次のぷよの色を取得
        next_color1 = game_logic.next_pair.colors[0]
        next_color2 = game_logic.next_pair.colors[1]
        
        # 簡易バージョンのぷよを描画（影・輪郭・光沢あり）
        # 1つ目のぷよ
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo1_x + 2, next_puyo1_y + 2), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(next_color1))
        painter.setPen(QPen(BLACK, 1))
        painter.drawEllipse(QPoint(next_puyo1_x, next_puyo1_y), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo1_x - 5, next_puyo1_y - 5), PUYO_SIZE // 4, PUYO_SIZE // 6)
        
        # 2つ目のぷよ
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo2_x + 2, next_puyo2_y + 2), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(next_color2))
        painter.setPen(QPen(BLACK, 1))
        painter.drawEllipse(QPoint(next_puyo2_x, next_puyo2_y), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo2_x - 5, next_puyo2_y - 5), PUYO_SIZE // 4, PUYO_SIZE // 6)
        
        # スコアパネル
        score_panel_x = next_panel_x
        score_panel_y = next_panel_y + next_panel_height + 20
        score_panel_width = next_panel_width
        score_panel_height = 60
        
        score_panel_rect = QRect(score_panel_x, score_panel_y, score_panel_width, score_panel_height)
        painter.fillRect(score_panel_rect, QColor(30, 30, 80))
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(score_panel_rect)
        
        # SCOREラベル
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(score_panel_x + 10, score_panel_y + 25, "SCORE")
        
        # スコア値
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        score_text = f"{game_logic.score}"
        
        # スコアテキストの中央揃え
        score_rect = QRect(score_panel_x, score_panel_y + 25, score_panel_width, 30)
        painter.drawText(score_rect, Qt.AlignCenter, score_text)
        
        # お邪魔ぷよカウンター
        ojama_panel_x = score_panel_x
        ojama_panel_y = score_panel_y + score_panel_height + 20
        ojama_panel_width = score_panel_width
        ojama_panel_height = 60
        
        ojama_panel_rect = QRect(ojama_panel_x, ojama_panel_y, ojama_panel_width, ojama_panel_height)
        painter.fillRect(ojama_panel_rect, QColor(30, 30, 80))
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(ojama_panel_rect)
        
        # OJAMAラベル
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(ojama_panel_x + 10, ojama_panel_y + 25, "OJAMA")
        
        # お邪魔ぷよの数
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        ojama_text = f"{game_logic.pending_ojama}"
        
        # お邪魔ぷよカウントの中央揃え
        ojama_rect = QRect(ojama_panel_x, ojama_panel_y + 25, ojama_panel_width, 30)
        painter.drawText(ojama_rect, Qt.AlignCenter, ojama_text)

        # 連鎖数の表示
        if game_logic.chain_count > 0:
            chain_label_x = board_x + (GRID_WIDTH * PUYO_SIZE) // 2
            chain_label_y = board_y - 15
            
            # 連鎖の背景枠（半透明）
            chain_width = 120
            chain_height = 40
            chain_rect = QRect(chain_label_x - chain_width // 2, chain_label_y - chain_height // 2, 
                            chain_width, chain_height)
            
            # グラデーション背景
            gradient = QLinearGradient(chain_rect.topLeft(), chain_rect.bottomRight())
            gradient.setColorAt(0, QColor(100, 100, 255, 150))
            gradient.setColorAt(1, QColor(50, 50, 150, 150))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(200, 200, 255), 2))
            painter.drawRoundedRect(chain_rect, 10, 10)
            
            # 連鎖テキスト
            painter.setPen(QPen(WHITE))
            painter.setFont(QFont('Arial', 16, QFont.Bold))
            
            # 文字に輪郭をつける
            shadow_offset = 1
            painter.setPen(QPen(QColor(0, 0, 0, 180)))
            painter.drawText(chain_rect.adjusted(shadow_offset, shadow_offset, 0, 0), 
                        Qt.AlignCenter, f"{game_logic.chain_count} れんさ!")
            
            painter.setPen(QPen(QColor(255, 255, 100)))
            painter.drawText(chain_rect, Qt.AlignCenter, f"{game_logic.chain_count} れんさ!")
        
        # ゲームオーバー表示
        if game_logic.game_over:
            game_over_rect = board_rect
            
            # 半透明の黒背景
            overlay = QColor(0, 0, 0, 180)
            painter.fillRect(game_over_rect, overlay)
            
            # ゲームオーバーの枠
            inner_rect = game_over_rect.adjusted(game_over_rect.width() // 4, game_over_rect.height() // 3,
                                            -game_over_rect.width() // 4, -game_over_rect.height() // 3)
            
            gradient = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomRight())
            gradient.setColorAt(0, QColor(100, 0, 0, 200))
            gradient.setColorAt(1, QColor(200, 0, 0, 200))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            painter.drawRoundedRect(inner_rect, 15, 15)
            
            # ゲームオーバーテキスト
            painter.setPen(QPen(WHITE))
            painter.setFont(QFont('Arial', 24, QFont.Bold))
            
            # 文字に輪郭をつける
            shadow_offset = 2
            painter.setPen(QPen(BLACK))
            painter.drawText(inner_rect.adjusted(shadow_offset, shadow_offset, 0, 0), 
                        Qt.AlignCenter, "GAME OVER")
            
            painter.setPen(QPen(QColor(255, 100, 100)))
            painter.drawText(inner_rect, Qt.AlignCenter, "GAME OVER")
            
            # リスタート案内
            restart_rect = QRect(
                inner_rect.left(),
                inner_rect.bottom() - 30,
                inner_rect.width(),
                30
            )
            
            painter.setFont(QFont('Arial', 12))
            painter.setPen(QPen(WHITE))
            painter.drawText(restart_rect, Qt.AlignCenter, "Press R to restart")

    def draw_vs_panel(self, painter):
        # 対戦情報パネル（中央に配置）
        vs_panel_width = 100
        vs_panel_height = 80
        vs_panel_x = (self.width() - vs_panel_width) // 2 + 350
        vs_panel_y = BOARD_PADDING + 20
        
        vs_panel_rect = QRect(vs_panel_x, vs_panel_y, vs_panel_width, vs_panel_height)
        
        # VSパネルの背景
        gradient = QLinearGradient(vs_panel_rect.topLeft(), vs_panel_rect.bottomRight())
        gradient.setColorAt(0, QColor(150, 0, 0, 200))
        gradient.setColorAt(1, QColor(200, 0, 0, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 200, 200), 2))
        painter.drawRoundedRect(vs_panel_rect, 15, 15)
        
        # VSテキスト
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 36, QFont.Bold))
        
        # 文字に輪郭をつける
        shadow_offset = 2
        painter.setPen(QPen(BLACK))
        painter.drawText(vs_panel_rect.adjusted(shadow_offset, shadow_offset, 0, 0), 
                    Qt.AlignCenter, "VS")
        
        painter.setPen(QPen(QColor(255, 255, 100)))
        painter.drawText(vs_panel_rect, Qt.AlignCenter, "VS")
        
        # 操作ガイドパネル（下部に配置）
        guide_panel_width = 300
        guide_panel_height = 80
        guide_panel_x = (self.width() - guide_panel_width) // 2 + 350
        guide_panel_y = BOARD_PADDING + GRID_HEIGHT * PUYO_SIZE - guide_panel_height
        
        guide_panel_rect = QRect(guide_panel_x, guide_panel_y, guide_panel_width, guide_panel_height)
        
        painter.fillRect(guide_panel_rect, QColor(30, 30, 80, 180))
        painter.setPen(QPen(QColor(100, 100, 200), 1))
        painter.drawRect(guide_panel_rect)
        
        # 操作方法の表示
        painter.setPen(QPen(QColor(200, 200, 255)))
        painter.setFont(QFont('Arial', 10))
        controls = [
            "方向キー: 移動・回転",
            "Z/X: 回転",
            "C: ちぎり",
            "R: リスタート"
        ]
        
        for i, control in enumerate(controls):
            painter.drawText(guide_panel_x + 10, guide_panel_y + 20 + i * 16, control)
    
    def draw_popping_puyos(self, painter, game_logic, board_x, board_y):
        for key, pop_state in game_logic.puyo_pop_state.items():
            # 時間に基づいて透明度を計算
            progress = 1.0 - (pop_state["time"] / game_logic.effect_duration)
            alpha = int(255 * (1.0 - progress))
            
            # 点滅のためのフラッシュ状態を計算
            flash_state = math.sin(progress * game_logic.flash_frequency * math.pi * 2) * 0.5 + 0.5
            
            # 点滅効果を明るさに適用
            flash_brightness = pop_state["brightness"] * (0.5 + flash_state * 0.5)
            
            # 元の色を取得
            base_color = pop_state["color"]
            
            # 明るさに基づいて色を変更（白に近づける）
            r, g, b = base_color.red(), base_color.green(), base_color.blue()
            white_blend = flash_brightness
            
            r = min(255, int(r * (1 - white_blend) + 255 * white_blend))
            g = min(255, int(g * (1 - white_blend) + 255 * white_blend))
            b = min(255, int(b * (1 - white_blend) + 255 * white_blend))
            
            color = QColor(r, g, b, alpha)
            
            # 現在のサイズを計算
            current_radius = int(PUYO_SIZE // 2 * pop_state["scale"])
            
            if current_radius > 0:
                # 中心座標を計算（整数に変換）
                center_x = int(board_x + pop_state["x"] * PUYO_SIZE + PUYO_SIZE // 2)
                center_y = int(board_y + pop_state["y"] * PUYO_SIZE + PUYO_SIZE // 2)

                # 消去中ぷよの影
                shadow_offset = 2
                shadow_color = QColor(0, 0, 0, alpha // 2)
                painter.setBrush(QBrush(shadow_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(center_x + shadow_offset, center_y + shadow_offset), 
                                current_radius, current_radius)
                
                # ぷよを描画
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(0, 0, 0, alpha), 1))  # 輪郭線
                painter.drawEllipse(QPoint(center_x, center_y), current_radius, current_radius)
                
                # 白い光沢も拡大縮小に合わせる
                highlight_size_x = current_radius * 0.7
                highlight_size_y = current_radius * 0.5
                highlight_offset_x = -current_radius * 0.2
                highlight_offset_y = -current_radius * 0.3
                
                highlight_alpha = min(255, int(alpha * (0.7 + flash_state * 0.3)))
                white_highlight = QColor(255, 255, 255, highlight_alpha)
                
                painter.setBrush(QBrush(white_highlight))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(
                    QPoint(center_x + int(highlight_offset_x), center_y + int(highlight_offset_y)),
                    int(highlight_size_x), int(highlight_size_y)
                )
                
                # 連鎖数に応じた輝きエフェクト
                chain = pop_state.get("chain", 1)
                if chain > 1 and flash_brightness > 0.5:
                    # 内側から外側に広がる輝きの輪
                    glow_phases = [0.3, 0.6, 0.9]  # 複数の輝きの位相
                    for glow_phase in glow_phases:
                        # 位相に基づいてサイズを計算（膨張と収縮を繰り返す）
                        phase_offset = (pop_state["phase"] * 3 + glow_phase) % 1.0
                        glow_size = int(current_radius * (0.6 + phase_offset * 0.8))
                        
                        if glow_size > 0:
                            # 連鎖数に応じた色
                            if chain <= 3:
                                glow_color = QColor(255, 255, 100, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                            elif chain <= 5:
                                glow_color = QColor(255, 100, 255, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                            else:
                                glow_color = QColor(100, 255, 255, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                            
                            # 輝きの輪を描画
                            ring_width = max(1, int(current_radius * 0.15))
                            painter.setPen(QPen(glow_color, ring_width))
                            painter.setBrush(Qt.NoBrush)
                            painter.drawEllipse(QPoint(center_x, center_y), glow_size, glow_size)
    
    def draw_star_effects(self, painter, game_logic, board_x, board_y):
        # 星形のエフェクトを描画
        for effect in game_logic.pop_effects:
            if effect.get("type") == "star":
                # 透明度を時間に基づいて変更
                alpha = int(255 * effect["time"] / game_logic.effect_duration)
                
                # 連鎖数を取得
                chain = effect.get("chain", 1)
                
                # 星のサイズを計算
                progress = 1.0 - (effect["time"] / game_logic.effect_duration)
                size_factor = 1.0
                
                # 時間経過で星のサイズも変更
                if progress < 0.5:
                    # 最初は大きくなる
                    size_factor = 0.5 + progress * 1.0
                else:
                    # 後半は小さくなる
                    size_factor = 1.5 - (progress - 0.5) * 1.0
                
                star_radius = effect["radius"] * size_factor * 0.6
                
                if star_radius > 0:
                    # 星の色 - 連鎖数に応じて色を変える
                    star_colors = [
                        QColor(255, 255, 0, alpha),  # 黄色
                        QColor(255, 0, 255, alpha),  # マゼンタ
                        QColor(0, 255, 255, alpha),  # シアン
                        QColor(255, 165, 0, alpha),  # オレンジ
                    ]
                    star_color = star_colors[(chain - 2) % len(star_colors)]
                    
                    # 星の中心座標を計算
                    center_x = int(board_x + effect["x"] * PUYO_SIZE + PUYO_SIZE // 2)
                    center_y = int(board_y + effect["y"] * PUYO_SIZE + PUYO_SIZE // 2)
                    
                    # 星を描画
                    points = []
                    for j in range(8):
                        point_angle = (j * 45 + 22.5) * 3.14159 / 180
                        dist = star_radius if j % 2 == 0 else star_radius * 0.4
                        points.append(QPoint(
                            int(center_x + math.cos(point_angle) * dist),
                            int(center_y + math.sin(point_angle) * dist)
                        ))
                    
                    painter.setBrush(QBrush(star_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawPolygon(points)
    
    def keyPressEvent(self, event):
       # プレイヤー1のキー入力を処理
       self.game_logic_p1.handle_key_press(event.key())
       
       # リスタートキー（両方のゲームをリセット）
       if event.key() == Qt.Key_R and (self.game_logic_p1.game_over or self.game_logic_p2.game_over):
           self.game_logic_p1.reset()
           self.game_logic_p2.reset()
           self.ai_player.reset()
       
       self.update()  # 再描画
    
    def update_game(self):
        # 時間差分の計算
        import time
        current_time = time.time()
        if self.last_time == 0:
            self.last_time = current_time
            dt = 0.016  # 初回は16msとしておく
        else:
            dt = current_time - self.last_time
        self.last_time = current_time
        
        # プレイヤー1のゲーム状態の更新
        self.game_logic_p1.update(dt)
        
        # プレイヤー1の操作中のペアのアニメーション更新
        if not self.game_logic_p1.falling_puyos and not self.game_logic_p1.game_over and not self.game_logic_p1.waiting_for_pop:
            self.game_logic_p1.current_pair.update(dt)
        
        # プレイヤー2（AI）のゲーム状態の更新
        self.game_logic_p2.update(dt)
        
        # AIの思考と行動
        self.ai_player.update(dt)
        
        # プレイヤー2の操作中のペアのアニメーション更新
        if not self.game_logic_p2.falling_puyos and not self.game_logic_p2.game_over and not self.game_logic_p2.waiting_for_pop:
            self.game_logic_p2.current_pair.update(dt)
        
        # 画面の更新
        self.update()

# 通常プレイモード用のゲームウィジェット
class PuyoGameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_logic = PuyoGameLogic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # 約60FPS
        self.last_time = 0
        self.setFocusPolicy(Qt.StrongFocus)  # キー入力を受け付けるようにする
        
        # ウィンドウサイズの設定
        board_width = GRID_WIDTH * PUYO_SIZE + BOARD_PADDING * 2
        board_height = GRID_HEIGHT * PUYO_SIZE + BOARD_PADDING * 2
        self.board_x = BOARD_PADDING
        self.board_y = BOARD_PADDING
        
        # サイドパネルのサイズ
        side_panel_width = 150
        
        # ウィンドウサイズを設定
        self.setMinimumSize(board_width + side_panel_width, board_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景を描画
        painter.fillRect(self.rect(), BG_COLOR)
        
        # ゲーム盤の背景
        board_rect = QRect(self.board_x, self.board_y, GRID_WIDTH * PUYO_SIZE, GRID_HEIGHT * PUYO_SIZE)
        painter.fillRect(board_rect, BOARD_BG_COLOR)
        
        # グリッドの描画 - より繊細なグリッド
        painter.setPen(QPen(GRID_COLOR, 1, Qt.DotLine))
        
        for x in range(GRID_WIDTH + 1):
            painter.drawLine(
                self.board_x + x * PUYO_SIZE, self.board_y,
                self.board_x + x * PUYO_SIZE, self.board_y + GRID_HEIGHT * PUYO_SIZE
            )
        
        for y in range(GRID_HEIGHT + 1):
            painter.drawLine(
                self.board_x, self.board_y + y * PUYO_SIZE,
                self.board_x + GRID_WIDTH * PUYO_SIZE, self.board_y + y * PUYO_SIZE
            )
        
        # 盤の枠線
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(board_rect)
        
        # グリッド上のぷよを描画
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.game_logic.grid[y][x] is not None:
                    self.game_logic.grid[y][x].draw(painter, self.board_x, self.board_y)
        
        # 消去中のぷよを描画
        self.draw_popping_puyos(painter)
        
        # 星形エフェクトを描画
        self.draw_star_effects(painter)
        
        # 現在のぷよペアを描画
        if not self.game_logic.falling_puyos and not self.game_logic.game_over and not self.game_logic.waiting_for_pop:
            self.game_logic.current_pair.draw(painter, self.board_x, self.board_y)
        
        # 次のぷよペアの表示 - 装飾枠追加
        next_panel_x = self.board_x + GRID_WIDTH * PUYO_SIZE + 20
        next_panel_y = self.board_y + 20
        next_panel_width = 100
        next_panel_height = 120
        
        # 「NEXT」パネル背景
        next_panel_rect = QRect(next_panel_x, next_panel_y, next_panel_width, next_panel_height)
        painter.fillRect(next_panel_rect, QColor(30, 30, 80))
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(next_panel_rect)
        
        # NEXTラベル
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(next_panel_x + 10, next_panel_y + 25, "NEXT")
        
        # 次のぷよを描画
        next_puyo1_x = next_panel_x + next_panel_width // 2
        next_puyo1_y = next_panel_y + 50
        next_puyo2_x = next_panel_x + next_panel_width // 2
        next_puyo2_y = next_panel_y + 90
        
        # 次のぷよの色を取得
        next_color1 = self.game_logic.next_pair.colors[0]
        next_color2 = self.game_logic.next_pair.colors[1]
        
        # 簡易バージョンのぷよを描画（影・輪郭・光沢あり）
        # 1つ目のぷよ
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo1_x + 2, next_puyo1_y + 2), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(next_color1))
        painter.setPen(QPen(BLACK, 1))
        painter.drawEllipse(QPoint(next_puyo1_x, next_puyo1_y), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo1_x - 5, next_puyo1_y - 5), PUYO_SIZE // 4, PUYO_SIZE // 6)
        
        # 2つ目のぷよ
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo2_x + 2, next_puyo2_y + 2), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(next_color2))
        painter.setPen(QPen(BLACK, 1))
        painter.drawEllipse(QPoint(next_puyo2_x, next_puyo2_y), PUYO_SIZE // 2 - 2, PUYO_SIZE // 2 - 2)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(next_puyo2_x - 5, next_puyo2_y - 5), PUYO_SIZE // 4, PUYO_SIZE // 6)
        
        # スコアパネル
        score_panel_x = next_panel_x
        score_panel_y = next_panel_y + next_panel_height + 20
        score_panel_width = next_panel_width
        score_panel_height = 60
        
        score_panel_rect = QRect(score_panel_x, score_panel_y, score_panel_width, score_panel_height)
        painter.fillRect(score_panel_rect, QColor(30, 30, 80))
        painter.setPen(QPen(QColor(100, 100, 200), 2))
        painter.drawRect(score_panel_rect)
        
        # SCOREラベル
        painter.setPen(QPen(WHITE))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(score_panel_x + 10, score_panel_y + 25, "SCORE")
        
        # スコア値
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        score_text = f"{self.game_logic.score}"
        
        # スコアテキストの中央揃え
        score_rect = QRect(score_panel_x, score_panel_y + 25, score_panel_width, 30)
        painter.drawText(score_rect, Qt.AlignCenter, score_text)
        
        # 連鎖数の表示 - より派手に
        if self.game_logic.chain_count > 0:
            chain_label_x = self.board_x + (GRID_WIDTH * PUYO_SIZE) // 2
            chain_label_y = self.board_y - 15
            
            # 連鎖の背景枠（半透明）
            chain_width = 120
            chain_height = 40
            chain_rect = QRect(chain_label_x - chain_width // 2, chain_label_y - chain_height // 2, 
                            chain_width, chain_height)
            
            # グラデーション背景
            gradient = QLinearGradient(chain_rect.topLeft(), chain_rect.bottomRight())
            gradient.setColorAt(0, QColor(100, 100, 255, 150))
            gradient.setColorAt(1, QColor(50, 50, 150, 150))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(200, 200, 255), 2))
            painter.drawRoundedRect(chain_rect, 10, 10)
            
            # 連鎖テキスト
            painter.setPen(QPen(WHITE))
            painter.setFont(QFont('Arial', 16, QFont.Bold))

            # 文字に輪郭をつける
            shadow_offset = 1
            painter.setPen(QPen(QColor(0, 0, 0, 180)))
            painter.drawText(chain_rect.adjusted(shadow_offset, shadow_offset, 0, 0), 
                        Qt.AlignCenter, f"{self.game_logic.chain_count} れんさ!")
            
            painter.setPen(QPen(QColor(255, 255, 100)))
            painter.drawText(chain_rect, Qt.AlignCenter, f"{self.game_logic.chain_count} れんさ!")
        
        # 操作方法パネル
        controls_panel_x = next_panel_x
        controls_panel_y = score_panel_y + score_panel_height + 20
        controls_panel_width = next_panel_width
        controls_panel_height = 120
        
        controls_panel_rect = QRect(controls_panel_x, controls_panel_y, controls_panel_width, controls_panel_height)
        painter.fillRect(controls_panel_rect, QColor(30, 30, 80, 180))
        painter.setPen(QPen(QColor(100, 100, 200), 1))
        painter.drawRect(controls_panel_rect)
        
        # 操作方法の表示
        painter.setPen(QPen(QColor(200, 200, 255)))
        painter.setFont(QFont('Arial', 8))
        controls = [
            "方向キー: 移動・回転",
            "Z/X: 回転",
            "C: ちぎり",
            "R: リスタート"
        ]
        
        for i, control in enumerate(controls):
            painter.drawText(controls_panel_x + 10, controls_panel_y + 20 + i * 24, control)
        
        # ゲームオーバー表示
        if self.game_logic.game_over:
            game_over_rect = board_rect
            
            # 半透明の黒背景
            overlay = QColor(0, 0, 0, 180)
            painter.fillRect(game_over_rect, overlay)
            
            # ゲームオーバーの枠
            inner_rect = game_over_rect.adjusted(game_over_rect.width() // 4, game_over_rect.height() // 3,
                                            -game_over_rect.width() // 4, -game_over_rect.height() // 3)
            
            gradient = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomRight())
            gradient.setColorAt(0, QColor(100, 0, 0, 200))
            gradient.setColorAt(1, QColor(200, 0, 0, 200))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            painter.drawRoundedRect(inner_rect, 15, 15)
            
            # ゲームオーバーテキスト
            painter.setPen(QPen(WHITE))
            painter.setFont(QFont('Arial', 24, QFont.Bold))
            
            # 文字に輪郭をつける
            shadow_offset = 2
            painter.setPen(QPen(BLACK))
            painter.drawText(inner_rect.adjusted(shadow_offset, shadow_offset, 0, 0), 
                        Qt.AlignCenter, "GAME OVER")
            
            painter.setPen(QPen(QColor(255, 100, 100)))
            painter.drawText(inner_rect, Qt.AlignCenter, "GAME OVER")
            
            # リスタート案内
            restart_rect = QRect(
                inner_rect.left(),
                inner_rect.bottom() - 30,
                inner_rect.width(),
                30
            )
            
            painter.setFont(QFont('Arial', 12))
            painter.setPen(QPen(WHITE))
            painter.drawText(restart_rect, Qt.AlignCenter, "Press R to restart")
    
    def draw_popping_puyos(self, painter):
        for key, pop_state in self.game_logic.puyo_pop_state.items():
            # 時間に基づいて透明度を計算
            progress = 1.0 - (pop_state["time"] / self.game_logic.effect_duration)
            alpha = int(255 * (1.0 - progress))
            
            # 点滅のためのフラッシュ状態を計算
            flash_state = math.sin(progress * self.game_logic.flash_frequency * math.pi * 2) * 0.5 + 0.5
            
            # 点滅効果を明るさに適用
            flash_brightness = pop_state["brightness"] * (0.5 + flash_state * 0.5)
            
            # 元の色を取得
            base_color = pop_state["color"]
            
            # 明るさに基づいて色を変更（白に近づける）
            r, g, b = base_color.red(), base_color.green(), base_color.blue()
            white_blend = flash_brightness
            
            r = min(255, int(r * (1 - white_blend) + 255 * white_blend))
            g = min(255, int(g * (1 - white_blend) + 255 * white_blend))
            b = min(255, int(b * (1 - white_blend) + 255 * white_blend))
            
            color = QColor(r, g, b, alpha)
            
            # 現在のサイズを計算
            current_radius = int(PUYO_SIZE // 2 * pop_state["scale"])

            if current_radius > 0:
               # 中心座標を計算（整数に変換）
               center_x = int(self.board_x + pop_state["x"] * PUYO_SIZE + PUYO_SIZE // 2)
               center_y = int(self.board_y + pop_state["y"] * PUYO_SIZE + PUYO_SIZE // 2)
               
               # 消去中ぷよの影
               shadow_offset = 2
               shadow_color = QColor(0, 0, 0, alpha // 2)
               painter.setBrush(QBrush(shadow_color))
               painter.setPen(Qt.NoPen)
               painter.drawEllipse(QPoint(center_x + shadow_offset, center_y + shadow_offset), 
                             current_radius, current_radius)
               
               # ぷよを描画
               painter.setBrush(QBrush(color))
               painter.setPen(QPen(QColor(0, 0, 0, alpha), 1))  # 輪郭線
               painter.drawEllipse(QPoint(center_x, center_y), current_radius, current_radius)
               
               # 白い光沢も拡大縮小に合わせる
               highlight_size_x = current_radius * 0.7
               highlight_size_y = current_radius * 0.5
               highlight_offset_x = -current_radius * 0.2
               highlight_offset_y = -current_radius * 0.3
               
               highlight_alpha = min(255, int(alpha * (0.7 + flash_state * 0.3)))
               white_highlight = QColor(255, 255, 255, highlight_alpha)
               
               painter.setBrush(QBrush(white_highlight))
               painter.setPen(Qt.NoPen)
               painter.drawEllipse(
                   QPoint(center_x + int(highlight_offset_x), center_y + int(highlight_offset_y)),
                   int(highlight_size_x), int(highlight_size_y)
               )
               
               # 連鎖数に応じた輝きエフェクト
               chain = pop_state.get("chain", 1)
               if chain > 1 and flash_brightness > 0.5:
                   # 内側から外側に広がる輝きの輪
                   glow_phases = [0.3, 0.6, 0.9]  # 複数の輝きの位相
                   for glow_phase in glow_phases:
                       # 位相に基づいてサイズを計算（膨張と収縮を繰り返す）
                       phase_offset = (pop_state["phase"] * 3 + glow_phase) % 1.0
                       glow_size = int(current_radius * (0.6 + phase_offset * 0.8))
                       
                       if glow_size > 0:
                           # 連鎖数に応じた色
                           if chain <= 3:
                               glow_color = QColor(255, 255, 100, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                           elif chain <= 5:
                               glow_color = QColor(255, 100, 255, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                           else:
                               glow_color = QColor(100, 255, 255, int(alpha * 0.5 * (1 - phase_offset) * flash_state))
                           
                           # 輝きの輪を描画
                           ring_width = max(1, int(current_radius * 0.15))
                           painter.setPen(QPen(glow_color, ring_width))
                           painter.setBrush(Qt.NoBrush)
                           painter.drawEllipse(QPoint(center_x, center_y), glow_size, glow_size)
   
    def draw_star_effects(self, painter):
        # 星形のエフェクトを描画
        for effect in self.game_logic.pop_effects:
            if effect.get("type") == "star":
                # 透明度を時間に基づいて変更
                alpha = int(255 * effect["time"] / self.game_logic.effect_duration)
                
                # 連鎖数を取得
                chain = effect.get("chain", 1)
                
                # 星のサイズを計算
                progress = 1.0 - (effect["time"] / self.game_logic.effect_duration)
                size_factor = 1.0
                
                # 時間経過で星のサイズも変更
                if progress < 0.5:
                    # 最初は大きくなる
                    size_factor = 0.5 + progress * 1.0
                else:
                    # 後半は小さくなる
                    size_factor = 1.5 - (progress - 0.5) * 1.0
                
                star_radius = effect["radius"] * size_factor * 0.6
                
                if star_radius > 0:
                    # 星の色 - 連鎖数に応じて色を変える
                    star_colors = [
                        QColor(255, 255, 0, alpha),  # 黄色
                        QColor(255, 0, 255, alpha),  # マゼンタ
                        QColor(0, 255, 255, alpha),  # シアン
                        QColor(255, 165, 0, alpha),  # オレンジ
                    ]
                    star_color = star_colors[(chain - 2) % len(star_colors)]
                    
                    # 星の中心座標を計算
                    center_x = int(self.board_x + effect["x"] * PUYO_SIZE + PUYO_SIZE // 2)
                    center_y = int(self.board_y + effect["y"] * PUYO_SIZE + PUYO_SIZE // 2)
                    
                    # 星を描画
                    points = []
                    for j in range(8):
                        point_angle = (j * 45 + 22.5) * 3.14159 / 180
                        dist = star_radius if j % 2 == 0 else star_radius * 0.4
                        points.append(QPoint(
                            int(center_x + math.cos(point_angle) * dist),
                            int(center_y + math.sin(point_angle) * dist)
                        ))
                    
                    painter.setBrush(QBrush(star_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawPolygon(points)
    
    def keyPressEvent(self, event):
        self.game_logic.handle_key_press(event.key())
        self.update()  # 再描画
    
    def update_game(self):
        # 時間差分の計算
        import time
        current_time = time.time()
        if self.last_time == 0:
            self.last_time = current_time
            dt = 0.016  # 初回は16msとしておく
        else:
            dt = current_time - self.last_time
        self.last_time = current_time
        
        # ゲーム状態の更新
        self.game_logic.update(dt)
        
        # 操作中のペアのアニメーション更新
        if not self.game_logic.falling_puyos and not self.game_logic.game_over and not self.game_logic.waiting_for_pop:
            self.game_logic.current_pair.update(dt)
        
        # 画面の更新
        self.update()

# メインウィンドウの修正
class PuyoGameWindow(QMainWindow):
    def __init__(self, vs_mode=True):
        super().__init__()
        
        self.vs_mode = vs_mode
        
        if vs_mode:
            self.setWindowTitle("ぷよぷよ通 対戦モード")
            self.game_widget = PuyoVsGameWidget(self)
        else:
            self.setWindowTitle("ぷよぷよ通 Qt版")
            self.game_widget = PuyoGameWidget(self)
        
        self.setCentralWidget(self.game_widget)
        
        # ウィンドウサイズの調整（対戦モードの場合は幅を広げる）
        if vs_mode:
            self.resize(540, 480)
        else:
            self.resize(640, 480)

# メイン関数
def main():
    app = QApplication(sys.argv)
    # デフォルトで対戦モードで起動
    window = PuyoGameWindow(vs_mode=True)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()