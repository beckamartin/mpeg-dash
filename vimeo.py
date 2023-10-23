#!/usr/bin/env python3

import json
import os
import pprint
import re
import shutil
import sys

import ffmpeg
import requests

from _utils import Downloads, _check_ffmpeg


# Folder directories
dir_temp = "temp/"
dir_video = "temp/video"
dir_audio = "temp/audio"
dir_downloads = "downloads/"


class Vimeo(Downloads):
    """'Vimeo' class is used to download videos from popular video-shraing platfrom vimeo.\n
    ---\n
    Command-Line use:\n
    $ python dash.py <URL>\n
    $ [360, 720, 1080 ..]\n
    $ Enter resolution: 720\n
    ---\n
    Import use:\n
    x = Vimeo(<URL>)\n
    print(x.list_quality())\n
    x.setting(720, "myvideo.mp4")\n
    x.download()\n
    """


    def __init__(self, url: str) -> None:
        """'__init__' initialize fundamental variables and checks for FFmpeg and status of URL.\n
        ---\n
        * url: str, user must provide valid URL for master JSON request.
        """
        super().__init__()
        _check_ffmpeg()

        self._master_url = None
        self._base_url = None
        self._clip_id = None
        self.set_basics = url

        self._data = None
        self.set_data = self._master_url

        self._select_res = None
        self._video_id = None
        self._audio_id = None
        self._segments = None
        self._segment_sufix = None
        self._audio_format = None
        self._dash_range = []
        self._file_name = None


    def setting(self, resolution: int, name: str=None):
        """'setting' method MUST be used BEFORE 'download'.\n
        Provides necessary variables for download.\n
        ---\n 
        * resolution: int, user must provide int of choosen resolution.\n
        If needed, call 'list_quality' to see the options.\n
        * name: str, optional parameter, user can choose the name of output file.\n
        If name = None, default name will be used (vimeo_<clip_id>_<resolution>.mp4)
        """

        # Set essentiasl variables according to user selected resolution     
        for n, video_res in enumerate(self.data.get("video")):
            if video_res.get("height") == resolution:
                self.select_res = n
                
                self.video_id = self.data["video"][self.select_res]["id"]
                self.audio_id = self.data["audio"][self.select_res]["id"]
                self.segments = len(self.data["video"][self.select_res]["segments"])
                self.segment_sufix = self.data["video"][self.select_res]["init_segment"].split("0")[1]
                self.audio_format = self.data["audio"][self.select_res]["format"]

                if self.audio_format == "dash":
                    self.dash_range.append(self.data["audio"][self.select_res].get("init_segment_range"))
                    self.dash_range.append(self.data["audio"][self.select_res].get("index_segment_range"))
                    for seg in self.data["audio"][self.select_res].get("segments"):
                        self.dash_range.append(seg.get("range"))

        self._check_res()

        # Set output file name according to user selected name or default name
        self.file_name = name

        if self.file_name != None:
            match = re.search(r"^(.*?)(\.mp4)?$", self.file_name)
            if match.group(1) == "":
                self.file_name = None
                print("Naming Error: Invalid Output File Name, Default Will Be Used)")
            else:
                if match.group(2) != ".mp4":
                    self.file_name = self.file_name + ".mp4"

        if self.file_name == None:
            self.file_name = "vimeo_" + self.clip_id + "_" + str(self.data["video"][self.select_res]["height"]) + "p" + ".mp4"


    def download(self):
        """'download' method MUST be used AFTER 'setting'.\n
        Downloads video in resolution selected in 'setting'.\n
        Output file can be found in './download/'.
        """

        # Check if user selected resolution, else exit
        self._check_res()

        # Check for temporary old files, deletes them, creates new diretories           
        if os.path.exists(dir_temp):
            shutil.rmtree(dir_temp)

        os.makedirs(dir_video, exist_ok=True)
        os.makedirs(dir_audio, exist_ok=True)
        os.makedirs(dir_downloads, exist_ok=True)

        # Send segment requests, download and concate binary video + audio
        full_video = b""
        full_audio = b""

        for i in range(0, self.segments+2):
            # Video (segmented URL requests)
            if i <= self.segments+1:
                current_url = self.base_url + self.clip_id + "/sep/video/" + self.video_id + "/chop/segment-" + str(i) + self.segment_sufix
                r = requests.get(current_url)
                with open(os.path.join(dir_video, "video-" + str(i)), "wb") as f:
                    f.write(r.content)
                full_video += r.content
            
            # Audio (segmented URL request)
            if self.audio_format == "mp42" and i <= self.segments+1:
                current_url = self.base_url + self.clip_id + "/sep/audio/" + self.audio_id + "/chop/segment-" + str(i) + self.segment_sufix
                r = requests.get(current_url)
                with open(os.path.join(dir_audio, "audio-" + str(i)), "wb") as f:
                    f.write(r.content)
                full_audio += r.content

            # Audio (static URL request, segmented header)
            elif self.audio_format == "dash":
                current_url = self.base_url + self.clip_id + "/parcel/audio/" + self.audio_id + self.segment_sufix
                header = {"Range": f"bytes={self.dash_range[i]}"}
                r = requests.get(current_url, headers=header)
                with open(os.path.join(dir_audio, "audio-" + str(i)), "wb") as f:
                    f.write(r.content)
                full_audio += r.content

            print(f"Download in Progress: {((i/(self.segments+2)) * 100):.0f} %", end="\r")

        # Write video and audio .mp4 files
        with open(dir_temp + "video.mp4", "wb") as f:
            f.write(full_video)

        with open(dir_temp + "audio.mp4", "wb") as f:
            f.write(full_audio)

        # Merg video + audio files via FFmpeg
        video_in = ffmpeg.input(dir_temp + "video.mp4")
        audio_in = ffmpeg.input(dir_temp + "audio.mp4")
        stream = ffmpeg.output(video_in, audio_in, os.path.relpath(self._path_downloads) + "\\" + self.file_name)
        ffmpeg.run(stream, overwrite_output=True)

        # Remove used temporary video + audio data
        shutil.rmtree(dir_temp)

        print(f"File '{self._file_name}' Created")


    def check_status(self):
        """'check_status' returns request status code from master URL.\n
        Can be used after creating instance of class object.
        """

        r = requests.get(self.master_url)
        return r.status_code


    def list_quality(self):
        """'list_quality' returns a list of all availible video resolutions.\n
        Can be used after creating instace of class object.
        """

        q = []
        try:
            for video in self.data.get("video"):
                q += {video.get("height")}
        except:
            print("Error: Missing Data")
            sys.exit(3)
        else: return sorted(q)


    def print_data(self, pretty: bool=True):
        """'print_data' returns JSON response from server.\n
        ---\n
        * pretty = True, returns pprint data (default).\n
        * pretty = False, returns print data.\n
        Can be used after creating instance of class object.
        """

        try:
            if pretty == True:
                return pprint.pprint(self.data)
            else: return print(self.data)
        except:
            print("Error: Missing Data")
            sys.exit(3)


    def dump_json(self):
        """'dump_json' creates .json file with data response from server.\n
        Can be used after creating instance of class object.
        """

        try:
            with open(self.clip_id + ".json", "w") as json_file:
                json.dump(self.data, json_file, indent=4)            
        except:
            print("Error: Missing Data")
            sys.exit(3)
        else: print(f"File '{self.clip_id}.json' Created")
    

    # Class getter-s, setter-s
    @property
    def master_url(self):
        return self._master_url
    
    @property
    def base_url(self):
        return self._base_url
    
    @property
    def clip_id(self):
        return self._clip_id
    
    @master_url.setter
    def set_basics(self, url):
        """'set_basics' uses re.search to catch master_url, base_url and clip_id.\n
        Also checks if the URL is usable or not.
        """

        try:
            match = re.search(r"^(((https://){1}(.+)(\.akamaized\.net/){1}(.+/))(.*?)(/sep/){1}(.+)(/master.json){1})(.+)?$", url)
            master_url, base_url, clip_id = match.group(1), match.group(2), match.group(7)
        except:
            print("Error: URL Not Acceptable")
            sys.exit(3)
        self._master_url = master_url
        self._base_url = base_url
        self._clip_id = clip_id


    @property
    def data(self):
        return self._data
    
    @data.setter
    def set_data(self, url):
        """'set_data' sends data request to server and looks for JSON response.\n
        Also checks if the URL is dead or response is an error.
        """

        r = requests.get(url)
        try:
            data = json.loads(r.text)
        except:
            print("Error: Bad Server Response (Dead URL or Other)")
            sys.exit(3)
        self._data = data
   

    @property
    def select_res(self):
        return self._select_res
    
    @select_res.setter
    def select_res(self, value):
        self._select_res = value
    
    @property
    def video_id(self):
        return self._video_id
    
    @video_id.setter
    def video_id(self, value):
        self._video_id = value
    
    @property
    def audio_id(self):
        return self._audio_id
    
    @audio_id.setter
    def audio_id(self, value):
        self._audio_id = value

    @property
    def segments(self):
        return self._segments
    
    @segments.setter
    def segments(self, value):
        self._segments = value

    @property
    def segment_sufix(self):
        return self._segment_sufix

    @segment_sufix.setter
    def segment_sufix(self, value):
        self._segment_sufix = value

    @property
    def audio_format(self):
        return self._audio_format

    @audio_format.setter
    def audio_format(self, value):
        self._audio_format = value

    @property
    def dash_range(self):
        return self._dash_range

    @dash_range.setter
    def dash_range(self, value):
        self._dash_range = value

    @property
    def file_name(self):
        return self._file_name
    
    @file_name.setter
    def file_name(self, value):
        self._file_name = value


    # Private functions
    def _check_res(self) -> None:
        """'_check_res' checks if user provided any select_res available for download.
        """

        try:
            if self.select_res == None:
                  raise ValueError
        except:
            print("Error: Bad or No Video Resolution Selected")
            sys.exit(2)


def main():
    """'main' function works only with argv as in a Command-Line Interface (CLI).\n
    ---\n
    Command-Line use:\n
    $ python dash.py <URL>\n
    $ [360, 720, 1080 ..]\n
    $ Enter resolution: 720\n
    """

    if len(sys.argv) != 2:
        print("Error: Invalid Number of User Arguments")
        sys.exit(2)

    x = Vimeo(sys.argv[1])
    print(x.list_quality())
    x.setting(int(input("Enter Resolution: ")))
    x.download()


if __name__ == "__main__":
    main()