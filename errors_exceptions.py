# Errors to raise

class InvalidTargetError(Exception):
    pass
class WorkingDirectoryError(InvalidTargetError):
    pass
class AlreadyEncryptedError(InvalidTargetError):
    pass
class CanNotDecryptError(InvalidTargetError):
    pass
class PathNotFoundError(InvalidTargetError):
    pass
class FileProccessingError(Exception):
    pass
class FileReadError(FileProccessingError):
    pass
class FileWriteError(FileProccessingError):
    pass
class DecryptionTokenError(FileProccessingError):
    pass
class FaceCamError(Exception):
    pass
class NoFaceDetected(FaceCamError):
    pass
class MultipileFacesDetected(FaceCamError):
    pass
class NoWebCamDetected(FaceCamError):
    pass
class WebCamError(FaceCamError):
    pass
class DataBaseError(Exception):
    pass
class InaccessbleDatabase(DataBaseError):
    pass
class FetchInfoError(DataBaseError):
    pass
class DecKeyNotFoundError(DataBaseError):
    pass