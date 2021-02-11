
import edgeiq
import cv2
import base64
import os

class VideoCamera(object):
    def __init__(self, video_file=""):
        if video_file != "":
            self.set_video(video_file)
        else:
            self.video = None

    def set_video(self, video_file=""):
        try:
            if video_file != "":
                self.is_file = True
                self.video = edgeiq.FileVideoStream(video_file, play_realtime=True)
            else:
                self.is_file = False
                self.video = edgeiq.WebcamVideoStream(cam=0)
            self.video.start()
        except RuntimeError:
            print("File does not exist, camera failed to start")
    
    def __del__(self):
        if self.video is not None:
            self.video.stop()

    def get_frame(self):
        if self.video is not None:
            image = self.update()
            frame = cv2.imencode('.jpg', image)[1].tobytes()
            return frame
        return None

    def update(self):
        """Get the most recent numpy array frame
        Returns:
            numpy array: image frame
        """
        if self.video is not None:
            if self.is_file and self.video.more():
                return self.video.read()
            else:
                return self.video.read()
        return None
