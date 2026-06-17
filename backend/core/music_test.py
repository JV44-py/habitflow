import pygame
import time

pygame.mixer.init()

pygame.mixer.music.load("song.mp3")  # replace with your mp3 filename
pygame.mixer.music.play()

print("Playing music...")

while pygame.mixer.music.get_busy():
    time.sleep(1)

print("Done!")