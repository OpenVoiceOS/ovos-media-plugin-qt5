from os.path import exists


def is_qtav_available():
    return exists("/usr/include/qt/QtAV") or \
           exists("/usr/lib/qt/qml/QtAV") or \
           exists("/usr/lib/libQtAV.so")
