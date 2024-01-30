# ovos-media-plugin-qt5

qt5 plugin for [ovos-media](https://github.com/OpenVoiceOS/ovos-media)

## Install

`pip install ovos-media-plugin-qt5`

## Configuration

```javascript
{
 "media": {

    // keys are the strings defined in "audio_players"
    "preferred_audio_services": ["qt5", "mplayer", "qt5", "cli"],

    // keys are the strings defined in "video_players"
    "preferred_video_services": ["qt5", "mplayer", "qt5", "cli"],

    // PlaybackType.AUDIO handlers
    "audio_players": {
        // qt5 player uses a headless qt5 instance to handle uris
        "qt5": {
            // the plugin name
            "module": "ovos-media-audio-plugin-qt5",

            // users may request specific handlers in the utterance
            // using these aliases
             "aliases": ["QT5"],

            // deactivate a plugin by setting to false
            "active": true
        }
    },

    // PlaybackType.VIDEO handlers
    "video_players": {
        // qt5 player uses a headless qt5 instance to handle uris
        "qt5": {
            // the plugin name
            "module": "ovos-media-video-plugin-qt5",

            // users may request specific handlers in the utterance
            // using these aliases
             "aliases": ["QT5"],

            // deactivate a plugin by setting to false
            "active": true
        }
    }
}
```