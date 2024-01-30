import os.path

from ovos_bus_client.apis.gui import GUIInterface
from ovos_bus_client.message import Message
from ovos_plugin_manager.templates.media import MediaBackend, AudioPlayerBackend, VideoPlayerBackend
from ovos_utils.log import LOG
from ovos_utils.ocp import OCP_ID, PlayerState, PlaybackType, find_mime


class QT5BaseService(MediaBackend):
    """ plugin to handle playback natively via mycroft-gui"""

    def __init__(self, config, bus=None):
        super().__init__(config, bus)
        # NOTE: we pass OCP_ID to share the namespace in ovos-gui
        # all values set in the UI for OCP should also be available here
        self.gui = GUIInterface(skill_id=OCP_ID, bus=bus,
                                ui_directories={"qt5": f"{os.path.dirname(__file__)}/qt5"})
        self.config = config
        self.bus = bus
        self.title = ""
        self.artist = ""
        self.image = ""
        self.playback_type = PlaybackType.UNDEFINED
        self.bus.on("ovos.common_play.status.response", self.handle_status)

    def supported_uris(self):
        return ['http', 'https']

    def handle_status(self, message):
        self.playback_type = message.data["playback_type"]
        self.title = message.data.get("title", "")
        self.artist = message.data.get("artist", "")
        self.image = message.data.get("image", "")

    def render(self, page, timeout=None):
        # self.gui synced with ovos-media due to shared OCP_ID
        self.gui["uri"] = self._now_playing  # for like/unlike
        if self.playback_type == PlaybackType.AUDIO:
            self.gui["audio_player_page"] = page
        elif self.playback_type == PlaybackType.VIDEO:
            self.gui["video_player_page"] = page
        elif self.playback_type == PlaybackType.WEBVIEW:
            self.gui["web_player_page"] = page

        pages = ["Home", page, "PlaylistView"]
        self.gui.show_pages(pages, 1,
                            override_idle=timeout or True,
                            override_animations=True,
                            remove_others=True)

    def track_info(self):
        """ Extract info of current track. """
        self.bus.wait_for_response(Message("ovos.common_play.status"))
        return {"title": self.title, "artist": self.artist}

    # qt5 gui player internals
    def play(self, repeat=False):
        """ Play playlist using qt5. """
        raise NotImplemented

    def stop(self):
        """ Stop qt5 playback. """

    def pause(self):
        """ Pause qt5 playback. """

    def resume(self):
        """ Resume paused playback. """

    def get_track_length(self):
        """
        getting the duration of the audio in milliseconds
        """
        return 0

    def get_track_position(self):
        """
        get current position in milliseconds
        """
        return 0

    def set_track_position(self, milliseconds):
        """
        go to position in milliseconds

          Args:
                milliseconds (int): number of milliseconds of final position
        """

    def seek_forward(self, seconds=1):
        """
        skip X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """

    def seek_backward(self, seconds=1):
        """
        rewind X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """

    def lower_volume(self):
        """Lower volume.

        This method is used to implement audio ducking. It will be called when
        OpenVoiceOS is listening or speaking to make sure the media playing isn't
        interfering.
        """

    def restore_volume(self):
        """Restore normal volume.

        Called when to restore the playback volume to previous level after
        OpenVoiceOS has lowered it using lower_volume().
        """


class QT5BasePlayerService(QT5BaseService):
    """ plugin to handle playback natively via mycroft-gui embedded player
    src: https://github.com/OpenVoiceOS/mycroft-gui-qt5/blob/dev/import/mediaservice.h
    """

    def __init__(self, config, bus=None, video=False):
        super().__init__(config, bus)
        self.is_video = video
        self.bus.on("gui.player.media.service.get.meta", self.handle_get_meta)
        self.bus.on("gui.player.media.service.sync.status", self.handle_gui_player_status)
        self.bus.on("gui.player.media.service.current.media.status", self.handle_gui_media_status)

    def handle_status(self, message):
        self.playback_type = message.data["playback_type"]
        if (self.playback_type == PlaybackType.AUDIO and not self.is_video) or \
                (self.playback_type == PlaybackType.VIDEO and self.is_video):
            self.title = message.data.get("title", "")
            self.artist = message.data.get("artist", "")
            self.image = message.data.get("image", "")
        else:
            self.title = self.artist = self.image = ""

    def handle_gui_player_status(self, message):
        """player state event from mycroft-gui
        https://github.com/OpenVoiceOS/mycroft-gui-qt5/blob/dev/import/mediaservice.cpp#L228
        """
        if (self.playback_type == PlaybackType.AUDIO and not self.is_video) or \
                (self.playback_type == PlaybackType.VIDEO and self.is_video):
            state = message.data["state"]
            if state == PlayerState.PAUSED:
                LOG.debug("QT5 player paused")
            elif state == PlayerState.STOPPED:
                LOG.debug("QT5 player stopped")
            else:
                LOG.debug("QT5 player running")
            self.bus.emit(Message("ovos.common_play.player.state",
                                  {"state": state}))

    def handle_gui_media_status(self, message):
        """media state event from mycroft-gui
        https://github.com/OpenVoiceOS/mycroft-gui-qt5/blob/dev/import/mediaservice.cpp#L281
        """
        if (self.playback_type == PlaybackType.AUDIO and not self.is_video) or \
                (self.playback_type == PlaybackType.VIDEO and self.is_video):
            state = message.data["status"]
            self.bus.emit(Message("ovos.common_play.media.state",
                                  {"state": state}))

    def handle_get_meta(self, message=None):
        """mycroft-gui native player is asking for metadata"""
        if (self.playback_type == PlaybackType.AUDIO and not self.is_video) or \
                (self.playback_type == PlaybackType.VIDEO and self.is_video):
            # sync metadata with OCP
            self.track_info()
            self.bus.emit(Message("gui.player.media.service.set.meta",
                                  {"artist": self.artist,
                                   "title": self.title,
                                   "image": self.image}))

    # qt5 gui player internals
    def supported_uris(self):
        return ['file', 'http', 'https']

    def stop(self):
        """ Stop qt5 playback. """
        if self._now_playing:
            self.bus.emit(Message("gui.player.media.service.stop"))
            self._now_playing = None
            return True
        return False

    def pause(self):
        """ Pause qt5 playback. """
        if self._now_playing:
            self.bus.emit(Message("gui.player.media.service.pause"))

    def resume(self):
        """ Resume paused playback. """
        if self._now_playing:
            self.bus.emit(Message("gui.player.media.service.resume"))


class QT5OCPAudioService(AudioPlayerBackend, QT5BasePlayerService):
    def __init__(self, config, bus=None):
        super().__init__(config, bus, video=False)

    # audio service
    def play(self, repeat=False):
        """ Play audio using qt5. """
        LOG.info('QT5Service Audio Play')
        self.playback_type = PlaybackType.AUDIO
        self.bus.emit(Message("gui.player.media.service.play", {
            "track": self._now_playing,
            "mime": find_mime(self._now_playing),
            "repeat": False}))
        self.render("OVOSAudioPlayer")


class QT5OCPVideoService(VideoPlayerBackend, QT5BasePlayerService):
    def __init__(self, config, bus=None):
        super().__init__(config, bus, video=True)

    def play(self, repeat=False):
        """ Play video using qt5. """
        LOG.info('QT5Service Video Play')
        self.playback_type = PlaybackType.VIDEO
        self.bus.emit(Message("gui.player.media.service.play", {
            "track": self._now_playing,
            "mime": find_mime(self._now_playing),
            "repeat": False}))
        self.render("OVOSVideoPlayer")


class QT5OCPWebService(VideoPlayerBackend, QT5BaseService):

    def handle_status(self, message):
        self.playback_type = message.data["playback_type"]
        if self.playback_type == PlaybackType.WEBVIEW:
            self.title = message.data.get("title", "")
            self.artist = message.data.get("artist", "")
            self.image = message.data.get("image", "")
        else:
            self.title = self.artist = self.image = ""

    def play(self, repeat=False):
        """ Play web using qt5. """
        LOG.info('QT5Service Web Play')
        self.playback_type = PlaybackType.WEBVIEW
        self.render("OVOSWebPlayer")
