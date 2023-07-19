# carol-heart

bv -> navidrome music


```py
import ffmpeg

def extract_audio_from_m4s(m4s_file, output_file):
    (
        ffmpeg
        .input(m4s_file) # can be bytes
        .output(output_file, acodec='copy') # must be filename
        .run()
    )

m4s_file = 'path/to/your/file.m4s'
output_file = 'path/to/output/audio.m4a'

extract_audio_from_m4s(m4s_file, output_file)
```