import pygame
import random
import os

CHANNEL_COUNT = 16
pygame.mixer.init(22050, -16, CHANNEL_COUNT, 64)
pygame.mixer.set_num_channels(CHANNEL_COUNT)
pygame.init()

channels = [pygame.mixer.Channel(channel) for channel in range(CHANNEL_COUNT)]

MUSIC_MAX_VOLUME = 1.0


def update():
    volume_control.update()
    music_volume.update()
    set_music_volume(MUSIC_MAX_VOLUME * music_volume.volume * volume_control.volume)


class VolumeControl:
    def __init__(self):
        self.volume = 1.0
        self.target_volume = 1.0
        self.fade_speed = 0.001

    def set_volume(self, volume):
        self.volume = volume
        self.target_volume = volume

    def fade_to(self, volume):
        self.target_volume = volume

    def update(self):
        if self.volume < self.target_volume:
            self.volume += self.fade_speed

            if self.volume > self.target_volume:
                self.volume = self.target_volume

        elif self.volume > self.target_volume:
            self.volume -= self.fade_speed

            if self.volume < self.target_volume:
                self.volume = self.target_volume

        set_music_volume(self.volume * MUSIC_MAX_VOLUME)


volume_control = VolumeControl()
music_volume = VolumeControl()


def load_music(path):
    pygame.mixer.music.load(pathify(path))


def play_music():
    pygame.mixer.music.play(-1)


def set_music_volume(volume):
    pygame.mixer.music.set_volume(volume)


def pathify(string):
    return os.path.join("sounds", string + ".wav")


def load(string):
    return pygame.mixer.Sound(pathify(string))


def play(sound, volume=1.0):
    channel = pygame.mixer.find_channel()
    if channel:
        channel.set_volume(volume * volume_control.volume)
        channel.play(sound)
