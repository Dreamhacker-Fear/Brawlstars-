"""
Auto-Dodge Lab  --  Python 3.9+, pygame 2.x
Run:  pip install pygame  &&  python dodge_lab.py

A self-contained top-down arena: 4 turrets fire aimed shots, a bot dodges them.
The bot only reads this game's own state. It does not touch any other program.

Keys
  B        bot on/off          G  debug rays on/off      R  reset
  WASD / arrows  move (when bot is off)
  1 / 2    reaction delay -/+ 20 ms
  3 / 4    perception noise -/+ 2 px
  5 / 6    turret fire rate -/+ 0.1x
"""
import math
import random
import sys

import pygame

S = 640            # arena size (px)
PS = 170           # player speed (px/s)
PR, BR = 12, 6     # player radius, projectile radius


def miss_p(hp):
    """Chance the bot never 'sees' a shot: 35% at 100% health, 0% at 10% health."""
    return 0.35 * min(1.0, max(0.0, (hp - 10) / 90))


class Game:
    def __init__(self):
        self.best = 0.0
        self.auto = True
        self.dbg = True
        self.rate = 1.0
        self.rd = 0.18      # reaction delay (s)
        self.nz = 10        # perception noise (px)
        self.reset()

    def reset(self):
        self.px = self.py = S / 2
        self.vx = self.vy = 0.0
        self.B = []         # projectiles: [x, y, vx, vy, life, blind]
        self.hist = []      # (time, [(x, y, vx, vy), ...]) snapshots the bot "sees"
        self.hp = 100
        self.hits = 0
        self.t = 0.0
        self.E = [[i * math.pi / 2 + 0.8, 1 + i * 0.35] for i in range(4)]  # [angle, cooldown]
        self.dir = (0.0, 0.0)
        self.cost = []
        self.tk = 0.0

    # ---- world ----
    @staticmethod
    def epos(e):
        return S / 2 + math.cos(e[0]) * 275, S / 2 + math.sin(e[0]) * 275

    def fire(self, e):
        ex, ey = self.epos(e)
        sp = 250 + random.random() * 60
        lt = math.hypot(self.px - ex, self.py - ey) / sp
        tx, ty = self.px + self.vx * lt, self.py + self.vy * lt      # lead the target
        a = math.atan2(ty - ey, tx - ex) + (random.random() - 0.5) * 0.2
        fan = (-0.28, 0, 0.28) if random.random() < 0.3 else (0,)
        for o in fan:
            self.B.append([ex, ey, math.cos(a + o) * sp, math.sin(a + o) * sp, 3.0,
                           random.random() < miss_p(self.hp)])

    # ---- bot ----
    def think(self):
        N, H, dt, safe = 16, 14, 0.05, 28
        snap = self.hist[0] if self.hist else None
        for h in self.hist:
            if h[0] <= self.t - self.rd:
                snap = h
            else:
                break
        lag = self.t - snap[0] if snap else 0.0
        src = snap[1] if snap else [(b[0], b[1], b[2], b[3]) for b in self.B if not b[5]]
        nz = self.nz
        V = [(x + random.uniform(-nz, nz), y + random.uniform(-nz, nz),
              vx * (1 + random.uniform(-.08, .08)), vy * (1 + random.uniform(-.08, .08)))
             for x, y, vx, vy in src]

        best, bd, cs = 1e9, self.dir, []
        for k in range(-1, N):
            d = (0.0, 0.0) if k < 0 else (math.cos(k / N * math.tau), math.sin(k / N * math.tau))
            cst, x, y = 0.0, self.px, self.py
            for s in range(1, H + 1):
                x = min(S - 14, max(14, x + d[0] * PS * dt))
                y = min(S - 14, max(14, y + d[1] * PS * dt))
                tt = s * dt + lag
                w = 1.5 - s / H
                for bx, by, bvx, bvy in V:
                    dd = math.hypot(x - (bx + bvx * tt), y - (by + bvy * tt))
                    if dd < safe:
                        cst += w * (8 if dd < PR + BR + 2 else (safe - dd) / safe * 2)
            m = min(x, y, S - x, S - y)
            if m < 70:
                cst += (70 - m) / 70                          # stay off the walls
            cst += math.hypot(x - S / 2, y - S / 2) / S * 0.4  # drift toward center
            if abs(d[0] - self.dir[0]) + abs(d[1] - self.dir[1]) > 0.01:
                cst += 0.06                                    # hysteresis
            cs.append((d, cst))
            if cst < best:
                best, bd = cst, d
        self.dir, self.cost = bd, cs

    # ---- update ----
    def step(self, dt, keys):
        self.t += dt
        self.tk -= dt
        if self.auto:
            self.hist.append((self.t, [(b[0], b[1], b[2], b[3]) for b in self.B if not b[5]]))
            while len(self.hist) > 1 and self.hist[1][0] <= self.t - self.rd:
                self.hist.pop(0)
            if self.tk <= 0:
                self.think()
                self.tk = max(0.05, self.rd * 0.6)
        else:
            x = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            y = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            l = math.hypot(x, y) or 1
            self.dir, self.cost = (x / l, y / l), []

        self.vx, self.vy = self.dir[0] * PS, self.dir[1] * PS
        self.px = min(S - PR, max(PR, self.px + self.vx * dt))
        self.py = min(S - PR, max(PR, self.py + self.vy * dt))

        for e in self.E:
            e[0] += 0.35 * dt
            e[1] -= dt * self.rate
            if e[1] <= 0:
                self.fire(e)
                e[1] = 1.1 + random.random() * 0.6

        for b in self.B:
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            b[4] -= dt
            if math.hypot(self.px - b[0], self.py - b[1]) < PR + BR:
                b[4] = 0
                self.hp -= 10
                self.hits += 1
                if self.hp <= 0:
                    self.best = max(self.best, self.t)
                    self.reset()
                    return
        self.B = [b for b in self.B if b[4] > 0 and -20 < b[0] < S + 20 and -20 < b[1] < S + 20]

    # ---- render ----
    def draw(self, scr, font):
        scr.fill((13, 15, 22))
        pygame.draw.rect(scr, (31, 42, 68), (0, 0, S, S), 2)
        if self.dbg and self.auto:
            for b in self.B:
                pygame.draw.line(scr, (90, 50, 50), (b[0], b[1]), (b[0] + b[2] * .7, b[1] + b[3] * .7), 1)
            for d, cst in self.cost:
                if d == (0.0, 0.0):
                    continue
                sel = d == self.dir
                col = pygame.Color(255, 255, 255) if sel else pygame.Color(0)
                if not sel:
                    col.hsla = (120 - 120 * min(1, cst / 4), 80, 50, 100)
                pygame.draw.line(scr, col, (self.px, self.py),
                                 (self.px + d[0] * 55, self.py + d[1] * 55), 4 if sel else 2)
        for e in self.E:
            x, y = self.epos(e)
            pygame.draw.rect(scr, (192, 57, 43), (x - 12, y - 12, 24, 24))
        for b in self.B:
            pygame.draw.circle(scr, (255, 176, 32), (int(b[0]), int(b[1])), BR)
        pygame.draw.circle(scr, (77, 163, 255), (int(self.px), int(self.py)), PR)

        pygame.draw.rect(scr, (34, 34, 34), (20, 14, 200, 10))
        pygame.draw.rect(scr, (62, 207, 110) if self.hp > 30 else (229, 72, 77), (20, 14, 2 * max(0, self.hp), 10))

        line1 = f"Health {self.hp}%"
        if self.auto:
            line1 += f"  |  bot hit chance {miss_p(self.hp) * 100:.0f}%"
        line1 += f"  |  hits {self.hits}  |  alive {self.t:.1f}s  |  best {max(self.best, self.t):.1f}s"
        line2 = (f"[B] bot {'ON' if self.auto else 'OFF'}  [G] debug  [1/2] reaction {self.rd * 1000:.0f}ms  "
                 f"[3/4] noise {self.nz}px  [5/6] fire x{self.rate:.1f}")
        scr.blit(font.render(line1, True, (230, 230, 240)), (8, S + 6))
        scr.blit(font.render(line2, True, (150, 150, 170)), (8, S + 28))


def main():
    pygame.init()
    scr = pygame.display.set_mode((S, S + 52))
    pygame.display.set_caption("Auto-Dodge Lab")
    font = pygame.font.SysFont("menlo,consolas,monospace", 14)
    clock = pygame.time.Clock()
    g = Game()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_b: g.auto = not g.auto
                elif k == pygame.K_g: g.dbg = not g.dbg
                elif k == pygame.K_r: g.reset()
                elif k == pygame.K_1: g.rd = max(0.0, g.rd - 0.02)
                elif k == pygame.K_2: g.rd = min(0.4, g.rd + 0.02)
                elif k == pygame.K_3: g.nz = max(0, g.nz - 2)
                elif k == pygame.K_4: g.nz = min(30, g.nz + 2)
                elif k == pygame.K_5: g.rate = max(0.5, g.rate - 0.1)
                elif k == pygame.K_6: g.rate = min(3.0, g.rate + 0.1)
        dt = min(0.033, clock.tick(60) / 1000)
        g.step(dt, pygame.key.get_pressed())
        g.draw(scr, font)
        pygame.display.flip()


if __name__ == "__main__":
    main()
