import imp
import subprocess
from functools import lru_cache
from socket import inet_ntoa

from . import settings


class PlayerAbstractionLayer:
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    NOT_RUNNING = "not_running"

    PLAYER_STATES = [PLAYING, PAUSED, NOT_RUNNING]

    def _execute_host_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """
        Executes a command on the Host:

        Requirements:
        * host is running sshd configured with a authorized_keys file
        * /keys/KEY_FILE.pub is in authorized_keys for user SSH_USERNAME
        """
        app_conf = settings.get_settings()
        # print("running subproc")
        try:
            proc = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-i",
                    app_conf.KEY_PATH,
                    f"{app_conf.SSH_USERNAME}@{app_conf.HOST_IP}",
                ]
                + command,
                capture_output=True,
                check=True,
            )
            return proc
        except subprocess.CalledProcessError as e:
            print(e)
            raise

    def get_song(self) -> dict[str, str]:
        raise NotImplementedError()

    def get_volume(self) -> int:

        raise NotImplementedError()

    def volume_up(self) -> None:
        raise NotImplementedError()

    def volume_down(self) -> None:
        raise NotImplementedError()

    def next_playlist(self) -> str:
        raise NotImplementedError()

    def next_song(self) -> dict[str, str]:
        raise NotImplementedError()

    def previous_song(self) -> dict[str, str]:
        raise NotImplementedError()

    def play_pause_toggle(self) -> str:
        raise NotImplementedError()

    def remove_from_playlist(self, id: int | None = None) -> None:
        raise NotImplementedError

    def get_song_time(self) -> dict[str, int | str]:
        raise NotImplementedError

    def get_player_status(self) -> str:
        raise NotImplementedError

    def get_all_playlists(self) -> list[str]:
        raise NotImplementedError

    def start_player(self) -> None:
        raise NotImplementedError

    def get_player_all_status(self) -> dict[str, str | int]:
        raise NotImplementedError
