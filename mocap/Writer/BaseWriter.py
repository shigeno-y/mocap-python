from pathlib import Path
from collections import defaultdict


class BaseWriter:
    def __init__(
        self,
        mainFileBasename: str,
        *,
        output_base=None,
        output_extension=".dummy",
        stride: int = 600,
        framesPerSecond=60,
        **kwargs,
    ):
        self._baseDir = Path(mainFileBasename)
        if output_base is not None:
            self._baseDir = Path(output_base) / self._baseDir.name
        self._mainFile = Path(self._baseDir.as_posix() + output_extension)

        self._stride = stride
        self._fps = framesPerSecond

        self.skeleton_ = list()
        self.timesamples_ = defaultdict(dict)
        self.frameTimes_ = list()
        self.initialFrame_ = None
        self.lastFrame_ = -1
        self._writeAnimationThreads = list()

    def close(self):
        raise NotImplementedError("close OVERRIDE REQUIRED")

    def updateSkeleton(self, skeleton: list):
        self.skeleton_ = skeleton

    def addTimesample(self, sample: dict):
        frame = sample["fnum"]
        if self.initialFrame_ is None:
            self.initialFrame_ = frame
        frame -= self.initialFrame_
        self.lastFrame_ = max(self.lastFrame_, frame)
        self.timesamples_[(frame // self._stride) * self._stride][frame] = sample
        self.frameTimes_.append(sample["uttm"])

        buckets = self.timesamples_.keys()
        if self.skeleton_ is not None and len(self.timesamples_[min(buckets)]) >= self._stride:
            fullBucket = min(buckets)
            anims = self.timesamples_.pop(fullBucket)
            self._writeAnimation(fullBucket, anims)

    def flushTimesample(self):
        for t in self.timesamples_.items():
            self._writeAnimation(*t)

        for t in self._writeAnimationThreads:
            t.join()

    def _writeAnimation(self, base, samples):
        raise NotImplementedError("__writeAnimation OVERRIDE REQUIRED")

    def _solveFPS(self):
        from statistics import fmean

        fps = 1.0 / fmean(map(lambda t: t[1] - t[0], zip(self.frameTimes_, self.frameTimes_[1:])))
        candidate = [
            30,
            50,
            60,
        ]
        if int(fps) in candidate:
            fps = int(fps)
        else:
            delta = list(map(lambda x: abs(x - fps), candidate))
            fps = int(candidate[delta.index(min(delta))])

        self._fps = fps


__all__ = ["BaseWriter"]
