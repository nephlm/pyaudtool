from datetime import timedelta

from .pal import PlayerAbstractionLayer

VALID_TAGS = ("album", "artist", "title")
VOLUME_INCREMENT = 5


class AudaciousControl(PlayerAbstractionLayer):
    DELIMITER = "|"

    def _get_tag(self, tag: str) -> str:
        if tag not in VALID_TAGS:
            raise ValueError(f"Not a valid tag: {tag=}")
        completed = self._execute_host_command(
            ["audtool", "current-song-tuple-data", tag]
        )
        return str(completed.stdout, "utf8")

    def _parse_song_info(self, song_info) -> dict[str, str]:
        parts = song_info.split(self.DELIMITER)
        if len(parts) == 3:
            artist, album, title = parts
        else:
            raise ValueError(
                'Song title format is not set correctly; Set to "${artist} | ${album} | ${title}"'
            )
        return {
            "artist": artist.strip(),
            "album": album.strip(),
            "title": title.strip(),
        }

    def get_song(self) -> dict[str, str]:
        completed = self._execute_host_command(["audtool", "current-song"])
        return self._parse_song_info(str(completed.stdout, "utf8"))

    def _multi_command(self, commands: list[str]):
        aud_commands = [f"audtool {x}; " for x in commands]
        command = [f"bash -c \"{' '.join(aud_commands)}\""]
        # print(command)

        return self._execute_host_command(command)

    def get_player_all_status(self) -> dict[str, str | int]:
        aud_sub_commands = [
            "current-song",
            "get-volume",
            "playback-status",
            "current-song-length-seconds",
            "current-song-output-length-seconds",
            "current-playlist-name",
        ]
        completed = self._multi_command(aud_sub_commands)
        raw_status = {}
        idx = 0
        keymap = aud_sub_commands
        for line in str(completed.stdout, "utf8").split("\n"):
            if line:
                raw_status[keymap[idx]] = line
            idx += 1
        return self._raw_status_to_output(raw_status, keymap)

    def _raw_status_to_output(
        self, raw: dict[str, str], keymap: list[str]
    ) -> dict[str, str | int]:
        output: dict[str, str | int] = {}
        output.update(self._parse_song_info(raw[keymap[0]]))
        output["volume"] = int(raw[keymap[1]])
        output["status"] = raw[keymap[2]]
        output["song_seconds"] = int(raw[keymap[3]])
        output["output_seconds"] = int(raw[keymap[4]])
        output["playlist_name"] = raw[keymap[5]]
        # print(output)
        return output

    def get_volume(self) -> int:
        completed = self._execute_host_command(["audtool", "get-volume"])
        return int(completed.stdout)

    def volume_up(self) -> None:
        self._adjust_volume(VOLUME_INCREMENT)

    def volume_down(self) -> None:
        self._adjust_volume(VOLUME_INCREMENT * -1)

    def _adjust_volume(self, adjustment: int) -> None:
        cmd = [
            "audtool",
            "set-volume",
            str(self.get_volume() + adjustment),
        ]
        _ = self._execute_host_command(cmd)

    def change_playlist(self, index: int) -> str:
        completed = self._execute_host_command(
            ["audtool", f"set-current-playlist {index}"]
        )
        completed = self._execute_host_command(["audtool", "current-playlist-name"])
        playlist_name = str(completed.stdout, "utf8")
        return playlist_name

    def next_playlist(self) -> str:
        completed = self._execute_host_command(["audtool", "current-playlist"])
        curr_playlist = int(completed.stdout)
        completed = self._execute_host_command(["audtool", "number-of-playlists"])
        playlist_count = int(completed.stdout)
        if curr_playlist + 1 > playlist_count:
            completed = self._execute_host_command(
                ["audtool", "set-current-playlist", "1"]
            )
        else:
            completed = self._execute_host_command(
                ["audtool", "set-current-playlist", str(curr_playlist + 1)]
            )
        completed = self._execute_host_command(["audtool", "current-playlist-name"])
        playlist_name = str(completed.stdout, "utf8")
        return playlist_name

    def next_song(self) -> dict[str, str]:
        _ = self._execute_host_command(["audtool", "playlist-advance"])
        return self.get_song()

    def previous_song(self) -> dict[str, str]:
        _ = self._execute_host_command(["audtool", "playlist-reverse"])
        return self.get_song()

    def play_pause_toggle(self) -> str:
        _ = self._execute_host_command(["audtool", "playback-playpause"])
        return self.get_player_status()

    def remove_from_playlist(self, song_id: int | None = None) -> None:
        if not song_id:
            completed = self._execute_host_command(["audtool", "playlist-position"])
            sid = completed.stdout
        else:
            sid = str(song_id)
        _ = self._execute_host_command(["audtool", "playlist-delete", sid])

    def get_all_playlists(self) -> list[str]:
        completed = self._execute_host_command(["audtool", "current-playlist"])
        curr_playlist = int(completed.stdout)
        completed = self._execute_host_command(["audtool", "number-of-playlists"])
        playlist_count = int(completed.stdout)

        aud_pre_commands = [
            "select-displayed",
        ]
        query_list = []
        for idx in range(1, playlist_count + 1):
            query_list += [
                f"set-current-playlist {idx}",
                "current-playlist-name",
            ]
        aud_post_commands = [f"set-current-playlist {curr_playlist}", "select-playing"]

        completed = self._multi_command(
            aud_pre_commands + query_list + aud_post_commands
        )
        playlists: list[str] = str(completed.stdout, "utf8").split("\n")
        if not playlists[-1]:
            playlists = playlists[:-1]

        return playlists

    def get_song_time(self) -> dict[str, int | str]:
        completed = self._execute_host_command(
            ["audtool", "current-song-length-seconds"]
        )
        time_seconds = int(completed.stdout)
        completed = self._execute_host_command(
            ["audtool", "current-song-output-length-seconds"]
        )
        output_time_seconds = int(completed.stdout)
        return {
            "time_seconds": time_seconds,
            "time_human": str(timedelta(seconds=time_seconds)),
            "output_time_seconds": time_seconds,
            "output_time_human": str(timedelta(seconds=output_time_seconds)),
        }

    def start_player(self) -> None:
        raise NotImplementedError
