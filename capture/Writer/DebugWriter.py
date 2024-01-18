from pprint import pprint


class DebugWriter:
    def __init__(
        self,
        *args,
        stride: int = 600,
        **kwargs,
    ):
        self.__stride = stride
        self.__skelCounter = stride + 1
        self.__animCounter = stride + 1

    def close(self):
        pass

    def updateSkeleton(self, skeleton: list):
        self.__skelCounter += 1
        if self.__skelCounter > self.__stride:
            pprint(skeleton)
            self.__skelCounter = 0

    def addTimesample(self, sample: dict):
        self.__animCounter += 1
        if self.__animCounter > self.__stride:
            pprint(sample)
            self.__animCounter = 0

    def flushTimesample(self):
        pass


__all__ = ["DebugWriter"]
