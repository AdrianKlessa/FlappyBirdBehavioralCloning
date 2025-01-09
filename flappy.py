import pandas as pd
import os
import pygame, sys, random
from pygame.time import Clock
from test_model import predict
screen = pygame.display.set_mode((1024, 1024))
gravity = 0.05
clock = Clock()

SAVE_HISTORY = False  # If True, gameplay history is saved to a file
MODEL_CONTROL = True  # If True, the model plays the game autonomously


class Bird:
    bird_surface = pygame.image.load("assets/bird.png")
    bird_surface = pygame.transform.scale(bird_surface, (64, 64))
    vertical_movement = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.bird_rect = self.bird_surface.get_rect(center=(x, y))

    def draw_and_update(self, dt):
        screen.blit(self.bird_surface, self.bird_rect)
        self.vertical_movement += gravity * dt
        self.vertical_movement = min(self.vertical_movement, 20)
        self.y += self.vertical_movement
        self.bird_rect.centery = self.y

    def jump(self):
        self.vertical_movement = -15


class Ground:
    ground_surface = pygame.image.load("assets/ground.png")
    ground_surface = pygame.transform.scale(ground_surface, (1024, 128))

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw_and_update(self, dt):
        screen.blit(self.ground_surface, (self.x, self.y))
        screen.blit(self.ground_surface, (self.x + 1024, self.y))
        self.x -= 0.1 * dt
        if self.x < -1024:
            self.x = 0


class Pipe:
    def __init__(self, x, y, manager):
        self.x = x
        self.y = y
        self.pipe_surface = manager.pipe_surface
        self.top_rect = self.pipe_surface.get_rect(midbottom=(x, y - 128))
        self.bottom_rect = self.pipe_surface.get_rect(midtop=(x, y + 128))

    def draw_and_update(self, dt):
        self.x -= 0.5 * dt
        self.top_rect.centerx = self.x
        self.bottom_rect.centerx = self.x
        screen.blit(self.pipe_surface, self.top_rect)
        screen.blit(self.pipe_surface, self.bottom_rect)


class PipeManager:
    pipes_list = []
    pipe_surface = pygame.image.load("assets/pipe.png")
    pipe_surface = pygame.transform.scale(pipe_surface, (96, 768))

    def __init__(self):
        self.pipes_list = []

    def add_pipe(self):
        random_y = random.choice([300, 512, 768])
        new_pipe = Pipe(1024, random_y, self)
        self.pipes_list.append(new_pipe)

    def draw_and_update(self, dt):
        for pipe in self.pipes_list:
            pipe.draw_and_update(dt)
        if len(self.pipes_list) < 1:
            return
        if self.pipes_list[0].x < -1024:
            self.pipes_list.pop(0)


def get_control_data(bird, pipe_manager):
    bird_rect = bird.bird_rect
    bird_y = bird_rect.centery
    if len(pipe_manager.pipes_list) < 1:
        return bird_y, bird.vertical_movement, 512, 2000
    next_pipe = pipe_manager.pipes_list[0]
    dist_to_pipe = next_pipe.x - bird_rect.centerx
    if dist_to_pipe < -100:
        next_pipe = pipe_manager.pipes_list[1]
        dist_to_pipe = next_pipe.x - bird_rect.centerx
    return [bird_y, bird.vertical_movement, next_pipe.y, dist_to_pipe]


class DataCollector:
    def __init__(self):
        self.gameplay_history = []

    def add_gameplay_frame(self, control_data, space_pressed):
        control_data = list(control_data)
        control_data.extend([space_pressed])
        self.gameplay_history.append(control_data)

    def clear_recent_history(self):
        if len(self.gameplay_history) > 200:
            self.gameplay_history = self.gameplay_history[:-200]

    def update_csv(self):
        if not SAVE_HISTORY:
            return
        if time_survived < 10:
            return
        df = pd.DataFrame(self.gameplay_history,
                          columns=["bird_y", "bird_vertical_movement", "pipe_y", "pipe_dist", "space_pressed"])
        if os.path.isfile("gameplay_history.csv"):
            csv_old = pd.read_csv("gameplay_history.csv")
            df_new = pd.concat([csv_old, df])
            df_new.to_csv("gameplay_history.csv", index=False)
        else:
            df.to_csv("gameplay_history.csv", index=False)
        self.gameplay_history = []


def check_collisions(bird_rect, pipe_manager):
    if bird_rect.bottom < 0 or bird_rect.top > 896:
        return True
    for pipe in pipe_manager.pipes_list:
        if bird_rect.colliderect(pipe.bottom_rect) or bird_rect.colliderect(pipe.top_rect):
            return True
    return False


background_surface = pygame.image.load("assets/Background.png").convert()
background_surface = pygame.transform.scale(background_surface, (1024, 1024))


def reset():
    ground = Ground(0, 896)
    bird = Bird(100, 100)
    pipe_manager = PipeManager()
    SPAWNPIPE = pygame.USEREVENT
    pygame.time.set_timer(SPAWNPIPE, 1200)
    return ground, bird, pipe_manager, SPAWNPIPE, 0


ground, bird, pipe_manager, SPAWNPIPE, time_survived = reset()
data_collector = DataCollector()

dt = clock.tick(60)
while True:
    SPACE_PRESSED = 0
    dt = clock.tick(60)
    time_survived += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            data_collector.update_csv()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bird.jump()
                SPACE_PRESSED = 1
        if event.type == SPAWNPIPE:
            pipe_manager.add_pipe()
    control_data = get_control_data(bird, pipe_manager)
    if MODEL_CONTROL:
        decision = predict(control_data)
        if decision>0.5:
            bird.jump()
    data_collector.add_gameplay_frame(control_data, SPACE_PRESSED)
    screen.blit(background_surface, (0, 0))
    if check_collisions(bird.bird_rect, pipe_manager):
        data_collector.clear_recent_history()
        data_collector.update_csv()
        ground, bird, pipe_manager, SPAWNPIPE, time_survived = reset()
    else:
        ground.draw_and_update(dt)
        bird.draw_and_update(dt)
        pipe_manager.draw_and_update(dt)
        pygame.display.update()
