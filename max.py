#!/usr/bin/env python3
"""Max catch trash game.
"""
import argparse
import os
import random
import sys

import pygame


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FRAME_RATE = 30
IMAGE_PATH = 'images'
SOUND_PATH = 'sounds'
OBJECTS_MAX = 40
MISSES_ALLOWED = 30
SPEED_MIN = 6
SPEED_MAX = 80
BUMP_FREQUENCY = FRAME_RATE // 3  # frames
BUMP_HEIGHT = 3
BONUSES = {
    'box': {
        'points': 100,
        'speed': 5,
        'sound': 'coin',
        },
    'present': {
        'points': 150,
        'speed': 15,
        'sound': 'coin',
        },
    'boot': {
        'points': 50,
        'speed': 7,
        'sound': 'coin',
        },
    'pillow': {
        'points': 100,
        'speed': 3,
        'sound': 'coin',
        },
    'soccerball': {
        'points': 50,
        'speed': 7,
        'sound': 'coin',
        },
    'thermos': {
        'points': 100,
        'speed': 7,
        'sound': 'coin',
        },
    }
SOUND_FILES = (  # name, file_name
    'coin',
    'powerup',
    'pause',
    'break_block-mod',
    )


class ImageStore():
    """Image store.
    """
    def __init__(self, path, ext='png'):
        """Initialize the store.

        Args:
            path: Path to image files.
            ext: File extension image files.
        """
        self._store = {}
        self._path = path
        self._ext = ext

    def get(self, name):
        """Get image object.

        If the image does not exist in the store, this will also try to
        add it first, but it is better to pre-add images as there is
        less delay.

        Args:
            name: Name of image to get.

        Returns:
            Image object, or None if object could not be found.
        """
        if name in self._store:
            image = self._store[name]
        else:
            image = self.add(name)
        return image

    def add(self, name):
        """Add image object to the store.

        Args:
            name: Name of image to add.

        Returns:
            Image object, or None if object could not be loaded.
        """
        image_path = os.path.join(self._path, '%s.%s' % (name, self._ext))
        image_object = pygame.image.load(image_path).convert_alpha()
        self._store[name] = image_object
        return image_object


class SoundStore():
    """Sound store.
    """
    def __init__(self, path, ext='wav'):
        """Initialize the store.

        Args:
            path: Path to sound files.
            ext: File extension of sound files.
        """
        self._store = {}
        self._path = path
        self._ext = ext

    def play(self, name):
        """Play sound object.

        If the sound does not exist in the store, this will also try to
        add it first, but it is better to pre-add sounds as there is
        less delay.

        Args:
            name: Name of sound to play.
        """
        if not name in self._store:
            self.add(name)
        self._store[name].play()

    def add(self, name):
        """Add sound object to the store.

        Args:
            name: Name of sound to add.

        Returns:
            sound object, or None if object could not be loaded.
        """
        sound_path = os.path.join(self._path, '%s.%s' % (name, self._ext))
        sound_object = pygame.mixer.Sound(sound_path)
        self._store[name] = sound_object
        return sound_object


class Character(pygame.sprite.Sprite):
    """All controllable things.
    """
    def __init__(self, kind, name, x_pos=0, y_pos=0, speed=SPEED_MIN):
        """Initialize character.

        Args:
            kind: Type of character (bullet, enemy, etc)
            name: Specific name of character.
            x_pos: X coordinate of character.
            y_pos: Y coordinate of character.
        """
        super().__init__()
        self.kind = kind
        self.name = name
        self.speed = speed

        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_inc = self.y_inc = 0

        self.image = IMAGES.get('%s/%s' % (kind, name))
        self.width, self.height = self.image.get_size()

        # Fetch the rectangle object that has the dimensions of the image
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.rect.center = self.x_pos, self.y_pos

    def display(self):
        """Draw the character image on the game board.
        """
        new_rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        return SCREEN.blit(self.image, new_rect)

    def update(self):
        """Update sprite.
        """
        self.x_pos += self.x_inc
        self.y_pos += self.y_inc
        self.rect.center = (self.x_pos, self.y_pos)
        self.display()


class Player(Character):
    """Player class.
    """
    def __init__(self, name='default'):
        """Initialize player.

        Args:
            name:
        """
        self.reset()
        super().__init__(
            'player', '%s%s-%s' % (name, self.emote, self.direction),
            self.x_pos, self.y_pos)

        self.images = {}
        for emote in ('', 'sad'):
            for direction in ('left', 'right'):
                self.images['%s-%s' % (emote, direction)] = IMAGES.get(
                    'player/%s%s-%s' % (name, emote, direction))
        self.y_orig = self.y_pos
        self.score = 0
        self.bump_count = 0
        self.misses = 0
        self.bonuses = {}
        for bonus in BONUSES:
            self.bonuses[bonus] = {}
            self.bonuses[bonus]['hit'] = 0
            self.bonuses[bonus]['miss'] = 0

    def get_input(self):
        """Get input from the user (keyboard)
        """
        game_over = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over = True
                elif event.key == pygame.K_p:
                    pause_game()
#                elif event.key == pygame.K_UP:
#                    self.y_inc = -self.speed
#                elif event.key == pygame.K_DOWN:
#                    self.y_inc = self.speed
                elif event.key == pygame.K_LEFT:
                    self.direction = 'left'
                    self.x_inc = -self.speed
                elif event.key == pygame.K_RIGHT:
                    self.direction = 'right'
                    self.x_inc = self.speed

            elif event.type == pygame.KEYUP:
                if self.x_inc < 0 and event.key == pygame.K_LEFT:
                    self.x_inc = 0
                elif self.x_inc > 0 and event.key == pygame.K_RIGHT:
                    self.x_inc = 0
#                elif event.key in (pygame.K_UP, pygame.K_DOWN):
#                    self.y_inc = 0
        return game_over

    def reset(self):
        """Reset position
        """
        self.x_pos = SCREEN_WIDTH // 2
        self.y_pos = SCREEN_HEIGHT * 2 // 3
        self.direction = 'left'
        self.emote = ''

    def lose(self):
        """Max loses.
        """
        self.emote = 'sad'

    def update(self):
        """Update Player.
        """
        if self.x_pos < self.width // 2:
            self.x_pos = self.width // 2
        elif self.x_pos > SCREEN_WIDTH - self.width // 2:
            self.x_pos = SCREEN_WIDTH - self.width // 2

        if self.y_pos < self.height // 2:
            self.y_pos = self.height // 2
        elif self.y_pos > SCREEN_HEIGHT - self.height // 2:
            self.y_pos = SCREEN_HEIGHT - self.height // 2

        if self.bump_count > BUMP_FREQUENCY:
            self.bump_count = 0
            self.y_pos += BUMP_HEIGHT
        elif self.x_inc:
            self.bump_count += 1
            self.y_pos = self.y_orig

        self.speed = self.score // 1000
        if self.speed < SPEED_MIN:
            self.speed = SPEED_MIN
        elif self.speed > self.width // 2:  #SPEED_MAX:
            self.speed = self.width // 2  #SPEED_MAX

        self.image = self.images['%s-%s' % (self.emote, self.direction)]
        super().update()


class Bonus(Character):
    """Bonus class.
    """
    def __init__(self, name=None, x_pos=0, y_pos=0):
        """Initialize bonus.
        """
        if not name:
            names = list(BONUSES.keys())
            name = random.choice(names)
        speed = BONUSES[name]['speed']
        super().__init__('bonus', name, x_pos, y_pos, speed)
        self.y_inc = random.randint(1, self.speed)
        self.x_pos = random.randint(self.width // 2,
                                    SCREEN_WIDTH - self.width // 2)
        self.y_pos = random.randint(-SCREEN_HEIGHT, -self.height)
        self.rotation = 0
        self.r_inc = random.randint(-5, 5)
        self.points = BONUSES[name]['points']
        self.sound = BONUSES[name]['sound']
        self.image_orig = self.image

    def update(self):
        self.rotation += self.r_inc
        self.rotation %= 360
        self.image = pygame.transform.rotate(self.image_orig, self.rotation)
        super().update()


def parse_args():
    """Parse user arguments and return as parser object.

    Returns:
        Parser object with arguments as attributes.
    """
    parser = argparse.ArgumentParser(description='Test basic functionality.')
    parser.add_argument('-i', '--infinite', action='store_true',
                        help='Enable infinite mode (no deaths).')
    args = parser.parse_args()
    return args


def show_stats(score, misses, misses_max):
    """Show stats
    """
    stats = GAME_FONT.render(
        ' %06d  (%s/%s)' % (score, misses, misses_max), True, (0, 0, 0))
    SCREEN.blit(stats, (0, 0))


def show_text(text, timer=-1, size=48, color=(255, 255, 0), py_key='any'):
    """Display text on screen for a given amount of time
    """
    text_pic = GAME_FONT.render(text, 1, color)
    # Center the input text (single line)
    half_size = (len(text) // 2) * (size // 3)
    # Position the text (single line) in the center of the screen
    text_position = ((SCREEN_WIDTH // 2) - half_size, SCREEN_HEIGHT // 2)
    SCREEN.blit(text_pic, text_position)
    pygame.display.flip()
    wait_for_keypress(py_key, timer)


def wait_for_keypress(py_key='any', timer=-1):
    """Waits for a keypress.

    Args:
        py_key: Pygame constant keyboard key referemce.
        timer: Amount of time to wait, in seconds.  -1 is infinite.
    """
    pygame.event.clear()
    while timer != 0:
        pygame.time.wait(1000)
        CLOCK.tick(10)
        if timer > 0:
            timer -= 1
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if py_key in ('any', event.key):
                    timer = 0


def pause_game():
    """Pause the game until the pause key is pressed again.
    """
    SOUNDS.play('pause')
    show_text('Paused', py_key=pygame.K_p)


def end_game():
    """End the game.
    """
    pygame.mixer.music.stop()
    pygame.mixer.music.load('sounds/game_over.wav')
    pygame.mixer.music.play()
    show_text('Game Over!')


def main():
    """The game itself.
    """
    exit_code = 0
    # To play music, simply select and play
    pygame.mixer.music.load('sounds/max_theme.wav')
    pygame.mixer.music.play(-1, 0.0)
    for sound in SOUND_FILES:
        SOUNDS.add(sound)
    bonuses = pygame.sprite.Group()
    player = Player('max')

    game_over = False
    while not game_over:
        SCREEN.fill((10, 0, 15))
        SCREEN.blit(IMAGES.get('background/site'), (0, 0))
        game_over = player.get_input()

        misses_allowed = (player.score // 500) + MISSES_ALLOWED
        objects_max = (player.score // 2000) * 5 + 10
        if objects_max > OBJECTS_MAX:
            objects_max = OBJECTS_MAX
        # Add bonuses
        if len(bonuses) < objects_max:
            bonus = Bonus()
            bonuses.add(bonus)

        # bonuses disappear when they float off screen.
        missed = [bonus for bonus in bonuses
                  if bonus.y_pos > SCREEN_HEIGHT + bonus.height]
        for bonus in missed:
            player.score -= bonus.points
            player.bonuses[bonus.name]['miss'] += 1
            player.misses += 1
            SOUNDS.play('break_block-mod')
            bonuses.remove(bonus)
        bonuses.update()

        if player.misses >= misses_allowed:
            game_over = True
            player.lose()

        player.update()

        # player touches a bonus
        hits = pygame.sprite.spritecollide(
            player, bonuses, True, pygame.sprite.collide_circle_ratio(.7))
        for bonus in hits:
            player.score += bonus.points
            player.bonuses[bonus.name]['hit'] += 1
            SOUNDS.play(bonus.sound)

        show_stats(player.score, player.misses, misses_allowed)
        CLOCK.tick(FRAME_RATE)
        pygame.display.flip()

    print(player.bonuses)
    end_game()
    return exit_code


if __name__ == '__main__':
    ARGS = parse_args()
    pygame.init()
    SCREEN = pygame.display.set_mode(SCREEN_SIZE)
    CLOCK = pygame.time.Clock()
    GAME_FONT = pygame.font.Font(None, 48)
    IMAGES = ImageStore(IMAGE_PATH, 'png')
    SOUNDS = SoundStore(SOUND_PATH, 'wav')
    EXIT_STATUS = main()
    pygame.quit()
    sys.exit(EXIT_STATUS)
