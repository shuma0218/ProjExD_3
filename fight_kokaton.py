import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5,0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load("fig/beam.png")  # ビーム画像をロード
        self.vx, self.vy = bird.dire  # こうかとんの向きを速度に設定
        theta = math.atan2(-self.vy, self.vx)  # 角度を計算（-vyで上下逆転を補正）
        deg = math.degrees(theta)  # 弧度法を度数法に変換
        self.img = pg.transform.rotozoom(self.img, deg, 1.0)  # 画像を回転
        self.rct = self.img.get_rect()

        # 初期位置をこうかとんの位置に基づいて設定
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct) 


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Score:
    """
    ゲームのスコア表示を管理するクラス
    """
    def __init__(self):
        """
        Scoreクラスのイニシャライザ
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)  # フォント設定
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # 初期スコア
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.img.get_rect()
        self.rect.center = (100, HEIGHT - 50)  # 左下に表示

    def update(self, screen: pg.Surface):
        """
        スコアを更新して画面に表示する
        引数 screen：描画する画面Surface
        """
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rect)

class Explosion:
    """
    爆発エフェクトを管理するクラス
    """
    def __init__(self, center: tuple[int, int]):
        """
        イニシャライザ
        引数 center：爆発位置の座標タプル
        """
        original = pg.image.load("fig/explosion.gif")
        self.images = [
            original, 
            pg.transform.flip(original, True, True)  # 上下左右反転
        ]
        self.index = 0  # 表示する画像のインデックス
        self.img = self.images[self.index]
        self.rct = self.img.get_rect()
        self.rct.center = center  # 爆発位置を設定
        self.life = 10  # 表示時間（爆発時間）

    def update(self, screen: pg.Surface):
        """
        爆発を演出するメソッド
        引数 screen：描画する画面Surface
        """
        if self.life > 0:
            self.life -= 1
            self.index = (self.index + 1) % len(self.images)  # 画像を交互に切り替え
            self.img = self.images[self.index]
            screen.blit(self.img, self.rct)




def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 爆弾をリストで生成
    beams = []
    explosions = []  # 爆発エフェクトのリストを作成
    clock = pg.time.Clock()
    score = Score()
    beam = None
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                 # スペースキー押下でBeamクラスのインスタンス生成
                 beams.append(Beam(bird))           
        screen.blit(bg_img, [0, 0])
        
        # 爆弾がNoneでない場合のみ判定
        for i, bomb in enumerate(bombs):
            if bomb and bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時の処理
                fonto = pg.font.Font(None, 80)  # フォントを作成
                txt = fonto.render("Game Over", True, (255, 0, 0))  # テキストを描画
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])  # テキストを画面中央に描画
                pg.display.update()
                time.sleep(1)  # 1秒間表示して終了
                return
    
        # ビームとの衝突判定
            for j, beam in enumerate(beams):
                if beam and bomb and beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb.rct.center))  # 爆発エフェクトを追加
                    bombs[i] = None  # 爆弾を消滅
                    beams[j] = None  # ビームを消滅
                    score.score += 1  # スコアを1点加算
        
        # 爆弾リストの更新（None以外の要素のみ残す）
        bombs = [bomb for bomb in bombs if bomb is not None]
         # ビームリストの更新（None以外かつ画面内の要素のみ残す）
        beams = [beam for beam in beams if beam and check_bound(beam.rct) == (True, True)]
        # 爆発エフェクトの更新（lifeが0より大きい要素のみ残す）
        explosions = [explosion for explosion in explosions if explosion.life > 0]

        if bombs == []:
            # ゲームクリア時の処理
            fonto = pg.font.Font(None, 80)  # フォントを作成
            txt = fonto.render("Game Clear", True, (255, 0, 0))  # テキストを描画
            screen.blit(txt, [WIDTH//2-150, HEIGHT//2])  # テキストを画面中央に描画
            pg.display.update()
            time.sleep(1)  # 1秒間表示して終了
            return

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:
            beam.update(screen) 
        for bomb in bombs:  
            bomb.update(screen)
        for explosion in explosions:
            explosion.update(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
