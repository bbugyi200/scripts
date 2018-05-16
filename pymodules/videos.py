import subprocess as sp

_rofi_cmd_fmt = 'rofi -p {} -width 90 -dmenu -i'


def get(opt):
    acceptable_opts = ['video', 'subs']
    assert opt in acceptable_opts, 'ERROR: opt must be in {}'.format(acceptable_opts)

    getter = {'video': _get_videos,
              'subs': _get_subs}

    return getter[opt]()


def _get_videos():
    ps = sp.Popen(['find', '/media/bryan/hercules/media/Entertainment/Videos', '-name', '*.avi', '-o', '-name', '*.mkv', '-o', '-name', '*.mp4'], stdout=sp.PIPE)

    try:
        out = sp.check_output(_rofi_cmd_fmt.format('Video File').split(), stdin=ps.stdout)
        return out.decode().strip()
    except sp.CalledProcessError as e:
        raise RuntimeError('No video file selected.')


def _get_subs():
    ps = sp.Popen(['find', '/home/bryan/Downloads', '/media/bryan/hercules/media/Entertainment/Videos', '-name', '*.srt'], stdout=sp.PIPE)

    try:
        out = sp.check_output(_rofi_cmd_fmt.format('Subtitle File').split(), stdin=ps.stdout)
        return out.decode().strip()
    except sp.CalledProcessError as e:
        return None
