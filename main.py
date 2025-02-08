import os
import sys
import time

import requests
import pygame
from yandex_music import Client

class YandexMusicPlayer:
    def __init__(self, token):
        self.client = Client(token).init()
        self.current_track = None
        self.is_playing = False
        self.temp_file = "temp.mp3"
        self.mixer_initialized = False  # Флаг инициализации микшера
        self.quality_choices = {
            1: {"codec": "mp3", "bitrate": 64},
            2: {"codec": "mp3", "bitrate": 128},
            3: {"codec": "mp3", "bitrate": 192},
            4: {"codec": "mp3", "bitrate": 320},
            5: {"codec": "aac", "bitrate": 64}
        }

    def select_quality(self, download_info):
        """Выбор качества воспроизведения"""
        print("\nДоступные варианты качества:")

        # Фильтруем и сортируем варианты
        available = []
        for idx, quality in self.quality_choices.items():
            variant = next(
                (d for d in download_info
                 if d.codec == quality["codec"]
                 and d.bitrate_in_kbps == quality["bitrate"]),
                None
            )
            if variant:
                available.append((idx, variant))

        # Показываем доступные варианты
        for idx, variant in available:
            print(f"{idx}. {variant.codec.upper()} {variant.bitrate_in_kbps} kbps")

        # Выбор пользователя
        while True:
            try:
                choice = int(input("Выберите качество (номер): "))
                if choice in [idx for idx, _ in available]:
                    selected = next(v for idx, v in available if idx == choice)
                    return selected
                else:
                    print("Неверный выбор!")
            except ValueError:
                print("Введите число!")

    def play_track(self, track_info):
        """Воспроизведение трека с выбором качества"""
        try:
            track = track_info.fetchTrack()
            download_info = track.get_download_info()

            if not download_info:
                print("Трек недоступен для скачивания.")
                return

            # Выбор качества
            selected_quality = self.select_quality(download_info)
            direct_link = selected_quality.get_direct_link()

            if self.mixer_initialized:
                pygame.mixer.quit()

            # Скачивание и воспроизведение
            if self.download_track(direct_link):
                pygame.mixer.init()
                pygame.mixer.music.load(self.temp_file)
                pygame.mixer.music.play()
                self.is_playing = True
                print(f"\nСейчас играет: {track.title} - {', '.join(a.name for a in track.artists)}")
                print(f"Качество: {selected_quality.codec.upper()} {selected_quality.bitrate_in_kbps}kbps")

        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")

    def get_liked_tracks(self):
        try:
            tracks = self.client.users_likes_tracks()
            return tracks.tracks
        except Exception as e:
            print(f"Ошибка при получении треков: {e}")
            return []

    def download_track(self, url):
        """Скачивание трека по URL"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                if os.path.exists(self.temp_file):
                    os.remove("temp.mp3")
                with open(self.temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                return True
            else:
                print(f"Ошибка скачивания: {response.status_code}")
                return False
        except Exception as e:
            print(f"Ошибка при скачивании трека: {e}")
            return False

    def player_controls(self):
        """Управление плеером"""
        while True:
            action = input("\nУправление (p - пауза, r - продолжить, s - остановить, q - выйти): ").lower()

            if action == 'p' and self.is_playing:
                pygame.mixer.music.pause()
                self.is_playing = False
            elif action == 'r' and not self.is_playing:
                pygame.mixer.music.unpause()
                self.is_playing = True
            elif action == 's':
                pygame.mixer.music.stop()
                self.is_playing = False
            elif action == 'q':
                pygame.mixer.music.stop()
                pygame.mixer.quit()

                # Пробуем удалить файл несколько раз с задержкой
                for _ in range(5):
                    try:
                        if os.path.exists(self.temp_file):
                            os.remove(self.temp_file)
                            break
                    except Exception as e:
                        time.sleep(0.1)  # Короткая пауза перед повторной попыткой
                self.run()


    def run(self):
        """Основной цикл программы"""
        liked_tracks = self.get_liked_tracks()

        if not liked_tracks:
            print("Нет лайкнутых треков или ошибка доступа!")
            return

        print("\nВаши лайкнутые треки:")
        for idx, track in enumerate(liked_tracks[:10], 1):  # Показываем первые 30 треков
            short_track = track.fetchTrack()
            print(f"{idx}. {short_track.title} - {', '.join(a.name for a in short_track.artists)}")

        while True:
            try:
                choice = int(input("\nВыберите номер трека (1-30) или 0 для выхода: "))
                if choice == 0:
                    sys.exit()
                elif 1 <= choice <= 30:
                    selected_track = liked_tracks[choice - 1]
                    self.play_track(selected_track)
                    self.player_controls()
                else:
                    print("Неверный выбор!")
            except ValueError:
                print("Введите число!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python yandex_music_player.py YOUR_OAUTH_TOKEN")
        sys.exit(1)

    token = sys.argv[1]
    player = YandexMusicPlayer(token)
    player.run()