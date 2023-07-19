import datetime as dt
import requests
import ffmpeg

from pathlib import Path
from pydantic import BaseModel
from mutagen.mp4 import MP4, MP4Cover


MUSIC_PATH = Path(__file__).parent / 'Data' / 'music'
TMP_PATH = Path(__file__).parent / 'tmp'


class Song(BaseModel):
    bv: str
    name: str
    album_name = 'Carol'
    atrist = '珈乐'
    
    # 後から取得
    cover_url: str | None
    audio_url: str | None # m4s format, need transform
    date: dt.date | None


def get_save_path(song: Song) -> str:
    filename = f"{song.date.strftime('%Y-%m-%d')}-{song.name}.m4a"
    return str(MUSIC_PATH / filename)


def get_tmp_path(song: Song) -> str:
    return str(TMP_PATH / song.bv)


def get_song_from_bv(bv, name) -> Song:
    # bilibili apiを使い、情報を取得
    info_data: dict = requests.get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}').json()['data']
    song = Song(bv=bv, name=name)
    pub_timestamp = int(info_data.get('pubdate'))
    song.date = dt.date.fromtimestamp(pub_timestamp)
    song.cover_url = info_data.get('pic')

    play_data: dict = requests.get(f"http://api.bilibili.com/x/player/playurl?fnval=16&bvid={bv}&cid={info_data['cid']}", allow_redirects=True).json()['data']
    song.audio_url = play_data['dash']['audio'][0]['baseUrl']
    print(song)
    return song


def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"例外が発生しました: {str(e)}")
    return wrapper


@handle_exception
def pull_song(song: Song) -> None:
    # m4aファイルを取得
    headers = {
        "User-Agent": "Mozilla/5.0` (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Range": "bytes=0-",
        "Referer": f"https://api.bilibili.com/x/web-interface/view?bvid={song.bv}",
        "Origin": "https://www.bilibili.com",
        "Connection": "keep-alive"
    }
    # res = requests.get(song.audio_url, headers=headers, allow_redirects=True)
    # print(res.status_code)
    m4sb = requests.get(song.audio_url, headers=headers, allow_redirects=True).content
    tmp_path = get_tmp_path(song)
    m4a_path = get_save_path(song)
    with open(tmp_path, 'wb') as f:
        f.write(m4sb)
    ffmpeg.input(tmp_path).output(m4a_path).run()
    m4a = MP4(m4a_path)

    # cover
    try:
        coverb = requests.get(song.cover_url).content
        m4a["covr"] = [MP4Cover(coverb, imageformat=MP4Cover.FORMAT_PNG if song.cover_url.endswith(
            'png') else MP4Cover.FORMAT_JPEG)]
    except Exception as e:
        # logger.warning(f'No cover supplyed. The error message is {e}')
        pass

    # date
    m4a.tags["\xa9day"] = [song.date.strftime("%Y-%m-%d")]

    # album title
    m4a.tags["\xa9alb"] = [song.album_name] 
    
    # name
    m4a.tags['\xa9nam'] = [song.name]

    # artist
    m4a.tags['\xa9ART'] = [song.atrist]

    m4a.save()
        
        
if __name__ == '__main__':
    while True:
        bv, name = input('bv: '), input('name: ')
        song = get_song_from_bv(bv, name)
        pull_song(song)
        print('ok, next')
