import cv2 as cv
import numpy as np
import face_recognition as fc
import time
import logs_system as log
import database_manager as dbm
import errors_exceptions as err


class facialRecognitionSystem():
    def __init__(self, logging_manger: log.Logging, db_manager: dbm.DataBaseManager = None):
        if not db_manager:
            db_manager = dbm.DataBaseManager()
        self.db_instance = db_manager
        self.log_instance = logging_manger
    
    # scans face for 3 frames with a 2 sec delay
    def _scan_face(self, counter = 3):
        # not how it will be handeled this is temporary
        
        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            raise err.NoWebCamDetected("Error: missing webcam")

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
            raise err.WebCamError("Error: no captred frames detected")
    
    
    # takes the frames and identifes the faces init
    #note the faces should go to database_manger to be pickeld into the database when needed else it will be used in compar_faces
    def _identify_faces(self, frame_images):
        face_encoding = []
        for frame in frame_images:
            faces_index = fc.face_locations(frame)
            
            if len(faces_index) > 1:
                raise err.MultipleFacesDetected("Error: multiple faces detected")
            
            if faces_index:
                encodings = fc.face_encodings(frame, faces_index)
                
                if encodings:
                    face_encoding.append(encodings[0])
        
        # might be unnecessary with the frames check in scan_face
        if not face_encoding:
            self.log_instance.announce_face_scan(False, "Facescan")
            raise err.NoFaceDetected("Error: no face detected")
        self.log_instance.announce_face_scan(True, "Facescan")
        return face_encoding

    # public function to manage scan_face and identify_faces
    def face_id_and_recog(self, counter = 3):
        frame_images = self._scan_face(counter)
        face_encoding = self._identify_faces(frame_images)
        return face_encoding

    # comapre the face data from scan_face with the face data from the database
    def compar_faces_with_db(self, face_encoding, tolerance_level=0.5):
        db_info: dbm.FaceData
        db_info = self.db_instance.fetch_personal_info_for_compar()
        
        if not db_info:
            raise err.FetchInfoError("Error: db fetch_personal_info_for_compar() return error")
        
        known_faces = [face.encoding for face in db_info]
        avg_encoding = np.mean(face_encoding, axis=0)

        matches = fc.compare_faces(known_faces, avg_encoding, tolerance_level)
        if matches:
            clean_matches = matches[0]
        if clean_matches.any():
            match_index = np.argmax(clean_matches)
            matched_user = db_info[match_index]
            self.log_instance.announce_face_scan(True, "Face mathcing")
            return matched_user.id
        
        self.log_instance.announce_face_scan(False, "Face mathcing")
        return None