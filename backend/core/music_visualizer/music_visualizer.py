import pygame
import time
import random
from rich.live import Live
from rich.panel import Panel

SONG = "Now Playing"
DURATION = 240

pygame.mixer.init()
pygame.mixer.music.load("music/disillusioned.mp3")
pygame.mixer.music.play()

start_time = time.time()

messages = [
    (21, "I cannot help but notice"),
    (23, "You find it's all lies, a thing you try"),
    (26, "You think this shit's bogus"),
    (28, "It isn't, you know this"),
    (41, "Seen in my peripheral"),
    (44, "You try to suffer bullshit"),
    (46, "You find it all difficult"),
    (48, "Giving up is typical"),
    (55, "And all typical of you"),
    (60, "And iIIIIIIIIIIm- I'm scared of gettin' older, it weighs upon my shoulders"),
    (73, "And you are scared of it too"),
    (78, "So if maybe we should get together, we'll take it all all better"),
    (83, "We should try something new, something new"),
    (88, "Couldn't help but notice you"),
    (93, "You smell like the roses"),
    (98, "Looking nice minded but no focus, focus"),
    (103, "But damn, you clean up the space"),
    (108, "I'm flying the folks to your place"),
    (113, "Everybody hates but not you"),
    (118, "Everybody speed our new boo"),
    (123, "Don't make me wait or I'll play"),
    (128, "Just stay, you gotta think that"),
    (133, "Don't make me wait or I'll play"),
    (138, "Just stay, you gotta think that"),
    (143, "Baby, please stay, please stay, please stay"),
    (148, "Oh (hey), oh (hey), oh (hey)"),
    (153, "And I'm- I'm scared of gettin' older, it weighs upon my shoulders"),
    (158, "And you are scared of it too"),
    (163, "So if maybe we should together, we'll take it all all better"),
    (168, "Take it all all better"),
    (173, "We should try something new"),
    (178, "Try something new"),
    (183, "Hop inside my Beamer with me, time to hit the road"),
    (188, "Tomorrow's modern boxes, tank of gas, girl, let's go"),
    (193, "Who cares where we end up, long as it's a place that's cool"),
    (198, "Pasadena, Malibu, let's go somewhere new"),
    (203, "Let's go to a board walk, watch the people walking by"),
    (208, "We'll make fun of their outfits, we'll be sitting next too get high"),
    (213, "Let's find a spot that's so secluded, do what lovers do"),
    (218, "I love being reclusive and I love being with you"),
]

def get_message(elapsed):
    current = ""
    for timestamp, text in sorted(messages, key=lambda x: x[0]):
        if elapsed >= timestamp:
            current = text
        else:
            break
    return current

def make_visualizer():
    elapsed = int(time.time() - start_time)
    mins = elapsed // 60
    secs = elapsed % 60
    progress = min(elapsed / DURATION, 1.0)
    progress_bar = "█" * int(progress * 40) + "░" * (40 - int(progress * 40))

    bars = " ".join("█" * random.randint(1, 6) for _ in range(15))

    current_message = get_message(elapsed)

    return Panel(
        f"[bold green]♫  {SONG}[/bold green]   [cyan]{mins:02}:{secs:02}[/cyan]\n\n"
        f"[green]{bars}[/green]\n\n"
        f"[cyan]{progress_bar}[/cyan]\n\n"
        f"[bold white]► {current_message}[/bold white]",
        title="Music Visualizer",
        border_style="green",
        expand=True,
    )

with Live(make_visualizer(), refresh_per_second=10) as live:
    while True:
        elapsed = time.time() - start_time
        live.update(make_visualizer())
        time.sleep(0.1)
        if elapsed >= DURATION:
            break

print("Finished.")