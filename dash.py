import sys
import re
import requests
import json
import os
import shutil
import subprocess


dir_temp = "temp/"
dir_video = "temp/video"
dir_audio = "temp/audio"
dir_down = "download/"

#-------------------------------------------------------------------------#

class vimeo:
    def __init__(self, url: str) -> None:
        try:
            match = re.search(r"^(((https://){1}(.+)(\.akamaized\.net/){1}(.+))(video/){1}(.+)(/master.json){1})(.+)?$", sys.argv[1])
            master_url, base_url = match.group(1), match.group(2)
        except:
            print("\nError: URL not acceptable")
            sys.exit()

        self._master_url = master_url
        self._base_url = base_url

        self._data = send_request(self._master_url)
        self._selected_res = select_res(self._data)

        self._clip_id = self._data["clip_id"]
        self._video_id = self._data["video"][self._selected_res]["id"]
        self._audio_id = self._data["audio"][self._selected_res]["id"]
        self._segments = len(self._data["video"][self._selected_res]["segments"])
        self._segments_sufix = self._data["video"][self._selected_res]["segments"][0]["url"].split("1")[1]

        self._file_name = "vimeo_" + self._clip_id

    def download(self):
        if os.path.exists(dir_temp):
            shutil.rmtree(dir_temp)

        os.makedirs(dir_video, exist_ok=True)
        os.makedirs(dir_audio, exist_ok=True)
        os.makedirs(dir_down, exist_ok=True)

        # Send segment request, download and concate binary video + audio
        full_video = b""
        full_audio = b""

        for i in range(0, self._segments+1):
            # Video
            current_url = self._base_url + "video/" + self._video_id + "/chop/segment-" + str(i) + self._segments_sufix
            r = requests.get(current_url)
            with open(os.path.join(dir_video, "video-" + str(i)), "wb") as f:
                f.write(r.content)
            full_video += r.content

            # Audio
            current_url = self._base_url + "audio/" + self._audio_id + "/chop/segment-" + str(i) + self._segments_sufix
            r = requests.get(current_url)
            with open(os.path.join(dir_audio, "audio-" + str(i)), "wb") as f:
                f.write(r.content)
            full_audio += r.content

            print(f"Download in Progress: {((i/self._segments) * 100):.0f} %", end="\r")

        # Write video and audio .mp4 files
        with open(dir_temp + "video.mp4", "wb") as f:
            f.write(full_video)

        with open(dir_temp + "audio.mp4", "wb") as f:
            f.write(full_audio)

        folder = os.listdir(dir_down)
        files = [file for file in folder if self._file_name in file]
        files = sorted(files)
        if files:
            match = re.search(r"^(.+[^_copy])([_copy]*)(\.mp4){1}$", files[-1])
            if match.group(2) == "":
                self._file_name = self._file_name + "_copy" + ".mp4"
            else:
                self._file_name = self._file_name + match.group(2) + "_copy" + ".mp4"
        else:
            self._file_name = self._file_name + ".mp4"

        # Merg video + audio files via FFmpeg
        subprocess.run("ffmpeg -i " + dir_temp + "video.mp4 " + "-i " + dir_temp + "audio.mp4 " + "-c copy " + dir_down + self._file_name, shell=True)
        # , stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        # Remove used video + audio data
        # shutil.rmtree(dir_temp)

        print("\nFinished")

    @property
    def url(self):
        return self._master_url
    
    @property
    def response_status(self):
        r = requests.get(self._master_url)
        return (r.status_code)
    
    @property
    def response_data(self):
        return self._data
    
    @property
    def parsed_response(self):
        return {"clip_id": self._clip_id,
                "video_id": self._video_id,
                "audio_id": self._audio_id,
                "segments": self._segments,
                "segments_sufix": self._segments_sufix
                }
    
    @property
    def response_json(self):
        with open(self._clip_id + ".json", "w") as json_file:
            json.dump(self._data, json_file, indent=4)
        
#-------------------------------------------------------------------------#

def send_request(url):
    r = requests.get(url)
    try:
        data = json.loads(r.text)
    except:
        print("\nError: Bad Server Response (dead URL)")
        sys.exit()
    return data

def select_res(data):
    for n, video in enumerate(data.get("video")):
        print(f"{n + 1} - {video.get('height')}p")
    return int(input("Enter selected number: ")) - 1

#-------------------------------------------------------------------------#

def main():
    if len(sys.argv) != 2:
        print("\nError: Invalid Number of User Arguments")
        sys.exit()

    x = vimeo(sys.argv[1])
    print(x.parsed_response)
    x.download()

#-------------------------------------------------------------------------#

if __name__ == "__main__":
    main()