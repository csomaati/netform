import sys
import time

class ProgressBar(object):
    """ProgressBar class holds the options of the progress bar.
    The options are:
        start   State from which start the progress. For example, if start is
                5 and the end is 10, the progress of this state is 50%
        end     State in which the progress has terminated.
        width   --
        fill    String to use for "filled" used to represent the progress
        blank   String to use for "filled" used to represent remaining space.
        format  Format
        incremental
    """
    def __init__(self, start=0, end=10, width=12, fill='=', blank='.', format='[%(fill)s>%(blank)s] %(progress)s%%[%(counter)s] %(time)s', incremental=True, time=False):
        super(ProgressBar, self).__init__()

        self.start = start
        self.end = end
        self.width = width
        self.fill = fill
        self.blank = blank
        self.format = format
        self.incremental = incremental
        self.timestamps = list()
        self.show_time = time
        self.step = 100 / float(width)  # fix
        self.reset()
        self.progress = 0

    def __add__(self, increment):
        self.timestamps.append(time.time())
        increment = self._get_progress(increment)
        if 100 > self.progress + increment:
            self.progress += increment
        else:
            self.progress = 100
        return self

    def __str__(self):
        try:
            time_diffs = [x[1] - x[0]
                          for x in zip(self.timestamps, self.timestamps[1:])]
            E_one_tic_time = sum(time_diffs) / len(time_diffs)
            remained = (100 - self.progress) * self.end * E_one_tic_time
            m, s = divmod(remained, 60)
            h, m = divmod(m, 60)
            remained = "%d:%02d:%02d" % (h, m, s)
            counter = "%04d/%04d" % ((self.progress * self.end)/100, self.end)
        except ZeroDivisionError:
            remained = '--:--:--'
            counter = '0000/%04d' % (self.end)

        progressed = int(self.progress / self.step)  # fix
        fill = progressed * self.fill
        blank = (self.width - progressed) * self.blank
        return self.format % {'fill': fill, 'blank': blank,
                              'progress': int(self.progress),
                              'time': remained,
                              'counter': counter}

    __repr__ = __str__

    def _get_progress(self, increment):
        return float(increment * 100) / self.end

    def reset(self):
        """Resets the current progress to the start point"""
        self.progress = self._get_progress(self.start)
        return self


class AnimatedProgressBar(ProgressBar):
    """Extends ProgressBar to allow you to use it straighforward on a script.
    Accepts an extra keyword argument named `stdout` (by default use sys.stdout)
    and may be any file-object to which send the progress status.
    """
    def __init__(self, *args, **kwargs):
        super(AnimatedProgressBar, self).__init__(*args, **kwargs)
        self.stdout = kwargs.get('stdout', sys.stdout)

    def show_progress(self):
        if hasattr(self.stdout, 'isatty') and self.stdout.isatty():
            self.stdout.write('\r')
        else:
            self.stdout.write('\n')
        self.stdout.write(str(self))
        self.stdout.flush()


class DummyProgressBar(AnimatedProgressBar):
    """Create a progressbar, which ommit everything"""
    def __init__(self, *args, **kwargs):
        super(DummyProgressBar, self).__init__(*args, **kwargs)

    def __add__(self, increment):
        return self

    def __str__(self):
        return ''

    def show_progress(self):
        pass

if __name__ == '__main__':
    p = AnimatedProgressBar(end=100, width=80)

    while True:
        p + 5
        p.show_progress()
        time.sleep(0.1)
        if p.progress == 100:
            break
    print #new line
