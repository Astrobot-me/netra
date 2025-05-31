import cv2 
import supervision as sv
import numpy as np
from typing import Optional
from ultralytics import YOLO


COLORS = sv.ColorPalette.DEFAULT


class VideoProcessor: 

    def __init__(
        self,
        source_weights_path: str,
        source_video_path: str,
        target_video_path: Optional[str] = None,
        confidence_threshold: float = 0.3,
        iou_threshold: float = 0.7,
    ) -> None:
        self.conf_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.source_video_path = source_video_path
        self.target_video_path = target_video_path

        self.model = YOLO(source_weights_path)

        # self.video_info = sv.VideoInfo.from_video_path(source_video_path)
        # self.zones_in = initiate_polygon_zones(ZONE_IN_POLYGONS, [sv.Position.CENTER])
        # self.zones_out = initiate_polygon_zones(ZONE_OUT_POLYGONS, [sv.Position.CENTER])

        self.box_annotator = sv.BoxAnnotator(color=COLORS)
        self.label_annotator = sv.LabelAnnotator(
            color=COLORS, text_color=sv.Color.BLACK
        )

    def process_video(self):
        frame_generator = sv.get_video_frames_generator(
            source_path=self.source_video_path
        )

        for frame in frame_generator:
            annotated_frame = self.process_frame(frame)
            cv2.imshow("Processed Video", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cv2.destroyAllWindows()

    def annotate_frame(self,frame:np.ndarray, detections:sv.Detections) -> np.ndarray:
        annotated_frame = frame.copy()
        annotated_frame = self.box_annotator.annotate(scene=frame,detections=detections)
        return annotated_frame 
        pass

    def process_frame(self,frame: np.ndarray) -> np.ndarray:
        results = self.model(
            frame, verbose=False, conf=self.conf_threshold, iou=self.iou_threshold
        )[0]
        detections = sv.Detections.from_ultralytics(results)
        return self.annotate_frame(frame=frame, detections=detections)
    



if __name__ == "__main__": 
    videoProcess = VideoProcessor(source_weights_path="./yolov5nu.pt",source_video_path="./video.mp4")
    videoProcess.process_video()