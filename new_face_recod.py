import cv2 as cv
import numpy as np
import face_recognition as fc
import time
import logs_system as log
import database_manager as dbm
import cv2 as cv
import numpy as np
import errors_exceptions as err
from dataclasses import dataclass

@dataclass
class FrameData:
    frame: np.ndarray
    faces_index : list[tuple[int, int, int, int]]

class facialRecognitionSystem():
    def __init__(self, logging_manger: log.Logging, db_manager: dbm.DataBaseManager = None):
        if not db_manager:
            db_manager = dbm.DataBaseManager()
        self.db_instance = db_manager
        self.log_instance = logging_manger
    
    # scans face for the required frames with a 2 sec delay
    def _scan_face(self, counter = 3):
        
        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            self.log_instance.announce_face_scan(False, "Facescan",error="missing webcam")
            raise err.NoWebCamDetected("missing webcam")

        frames = []
        last_capture_time = time.time()
        delay = 2

        while len(frames) < counter:

            ret, frame = cap.read()
       
            if not ret:
                continue

            cv.imshow("Capturing Face", frame)
            cv.waitKey(1)
            current_time = time.time()

            if current_time - last_capture_time >= delay:
                rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                frames.append(rgb_frame)
                last_capture_time = current_time
        
        cap.release()
        cv.destroyAllWindows()
        if frames:
            return frames
        else:
            self.log_instance.announce_face_scan(False, "Facescan",error="no captred frames detected")
            raise err.WebCamError("no captred frames detected")
    
    def _run_checks(self, frame_images, allowed_bad_frames=2, sharpened = False):
        frames = []

        for frame in frame_images:
            # checks the number of faces detected
            faces_index = fc.face_locations(frame)
            if len(faces_index) < 1:
                self.log_instance.announce_face_scan(False, "Facescan",error="no face detected")
                raise err.NoFaceDetected("no face detected")
            if len(faces_index) > 1:
                self.log_instance.announce_face_scan(False, "Facescan",error="multiple faces detected")
                raise err.MultipleFacesDetected("multiple faces detected")
            
            try:
                self._check_lighting(frame=frame)
                self._check_blur(frame=frame)
                

                # check detected landmarkes
                landmarks_list = fc.face_landmarks(frame, faces_index)

                if not landmarks_list:
                    allowed_bad_frames -= 1
                    if allowed_bad_frames <= 0:
                        self.log_instance.announce_face_scan(False, "Facescan",error="missing all landmarks")
                        raise err.Nolandmarks("too many bad frames. try again.")
                    continue
                
                landmarks = landmarks_list[0]
                
                if not self._check_landmarks(landmarks=landmarks):
                    allowed_bad_frames -= 1
                    if allowed_bad_frames <= 0:
                        self.log_instance.announce_face_scan(False, "Facescan",error="missing some landmarks")
                        raise err.Nolandmarks("too many bad frames. try again.")
                    continue
                
                # only adds good frames
                frames.append(FrameData(frame=frame, faces_index=faces_index))

            except err.FaceCamError as e:
                # check the tolerance for the bad frames
                allowed_bad_frames -= 1
                if allowed_bad_frames <= 0:
                    
                    # attempt to batch shapen all frames to meet the requirments 
                    if not sharpened:
                        self.log_instance.generic_error(f"too many bad frames attempting sharpening")
                        sharpened = True
                        try:
                            frames = self._sharpen(image_set=frame_images)
                            frames_set = self._run_checks(frame_images=frames, allowed_bad_frames=2, sharpened=sharpened)
                            self.log_instance.generic_log("Sharpening was successful")
                            return frames_set
                        except err.FaceCamError as e:
                            raise err.FaceCamError(e)
                    
                    # end and document the attmept
                    self.log_instance.announce_face_scan(False, "Facescan",error=e)
                    raise err.FaceCamError(e)
                continue
        
        self.log_instance.generic_log(f"number of good frames: {len(frames)}, total frames: {len(frame_images)}")
        return frames

    # takes the frames and identifes the faces init
    #note the faces should go to database_manger to be pickeld into the database when needed else it will be used in compar_faces
    def _identify_faces(self, frames_set):
        face_encoding = []
        
        for frame in frames_set:
            frame: FrameData
            faces_index = frame.faces_index
            frame = frame.frame
            
            if faces_index:
                encodings = fc.face_encodings(frame, faces_index)
                
                if encodings:
                    face_encoding.append(encodings[0])
        
        # might be unnecessary with the frames check in scan_face
        if not face_encoding:
            self.log_instance.announce_face_scan(False, "Facescan")
            raise err.NoFaceDetected("no face detected")
        self.log_instance.announce_face_scan(True, "Facescan")
        return face_encoding

    # public function to manage scan_face and identify_faces
    def face_id_and_recog(self, counter = 5):
        frame_images = self._scan_face(counter)
        frames_set = self._run_checks(frame_images)
        face_encoding = self._identify_faces(frames_set)
        return face_encoding

    # comapre the face data from scan_face with the face data from the database
    def compar_faces_with_db(self, face_encoding, tolerance_level=0.4):
        db_info = self.db_instance.fetch_personal_info_for_compar()
        if not db_info:
            self.log_instance.announce_face_scan(False, "Face mathcing", error="db fetch_personal_info_for_compar() return error")
            raise err.FetchInfoError("db fetch_personal_info_for_compar() return error")
        
        known_faces = [face.encoding for face in db_info]
        avg_encoding = np.mean(face_encoding, axis=0)
        avg_encoding = np.array(avg_encoding).flatten()

        matches = fc.compare_faces(known_faces, avg_encoding, tolerance_level)
        if matches:
            if True in matches:
                match_index = matches.index(True)
                matched_user = db_info[match_index]
                self.log_instance.announce_face_scan(True, "Face mathcing")
                return matched_user.id
        
        self.log_instance.announce_face_scan(False, "Face mathcing")
        return None

    # check functions

    # make sure the lighting is good
    def _check_lighting(self, frame, min = 95, max = 245):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        lighting_mean = np.mean(gray)
       
        if lighting_mean < min or lighting_mean > max:
            self.log_instance.generic_log(F"frame lighting level: {lighting_mean}. required levels: min:{min}, max:{max}")
            raise err.FrameTooDark("lighting is too dark/bright")
        else:
            return True
    # make sure the image is clear
    def _check_blur(self, frame, threshold = 65):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        blur = cv.Laplacian(gray, cv.CV_64F).var()
        
        if blur < threshold:
            self.log_instance.generic_log(f"frame clearness level: {blur}, min required: {threshold}")
            raise err.FrameTooBlury("image not clear.")
        else:
            return True
    # make sure all the important landmarks are there
    def _check_landmarks(self, landmarks):
        required_landmarks = ["left_eye", "right_eye", "nose_bridge", "nose_tip", "top_lip", "bottom_lip"]
        for part in required_landmarks:
            if part not in landmarks:
                return False
            if len(landmarks[part]) < 2:
                return False
        return True

    # sharpen frame, incase it was close enough to the threshold
    def _sharpen_helper(self, frame, strength = 0.1):
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]], dtype=np.float32)
        sharpened = cv.filter2D(frame, -1, kernel)
        output_frame = cv.addWeighted(frame, 1 - strength, sharpened, strength, 0)
        return output_frame
    # shapening flow
    def _sharpen(self, image_set):
        frame_set = []
        for frame in image_set:
            data = self._sharpen_helper(frame)
            frame_set.append(data)    
        return frame_set