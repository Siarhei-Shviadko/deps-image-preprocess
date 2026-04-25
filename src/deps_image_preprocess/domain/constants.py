from enum import Enum


class ImageExtensionEnum(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    TIF = "tif"


class ImagePreprocessorEnum(str, Enum):
    GRAYSCALING = "grayscaling"
    BLURRING = "blurring"
    THRESHOLDING = "thresholding"
    ROTATION = "rotation"
    ORIENTATION = "orientation"


class ImageOrientationEnum(int, Enum):
    DO_NOTHING = 0
    ROTATE_90_CLOCKWISE = 90
    ROTATE_180 = 180
    ROTATE_90_COUNTERCLOCKWISE = 270
