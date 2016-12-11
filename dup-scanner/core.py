""" Program for find dups in directory
"""
import argparse
import logging
from typing import Dict, List, Iterable

from hashlib import md5
from os import walk
from os.path import isdir, join, getsize, isfile
from functools import partial


class FileInfo:
    """ File descriptor """

    def __init__(self, file_path: str) -> None:
        logging.debug('new file for path %s' % file_path)
        self.path = file_path
        self.size = getsize(file_path)
        self.md5 = calc_md5(file_path)

    def __repr__(self) -> str:
        return "{} {} -{}-".format(self.path, self.size, self.md5)


def calc_md5(file_path: str, full: bool = False) -> str:
    """ Calculate md5 hash for by for file begin """
    if not full:
        with open(file_path, 'rb') as f:
            buf = f.read(2 ** 20)
            return md5(buf).hexdigest()
    else:
        with open(file_path, mode='rb') as f:
            d = md5()
            for buf in iter(partial(f.read, 2 ** 20), b''):
                d.update(buf)
            return d.hexdigest()


class DirectoryScanner:
    """Hold info about all scanned files"""

    def __init__(self, dir_path: str, ignore: bool) -> None:
        """ C-tor
        Args:
            dir_path: path to scan directory
        """
        if not isdir(dir_path):
            raise NotADirectoryError('--path arg should be directory, %s' % dir_path)
        self.dir_path = dir_path
        if ignore:
            self.min_size = 2 ** 17
        else:
            self.min_size = 0
        self.scanned_info = {}  # type: Dict[str, List[FileInfo]]

    def traverse(self) -> None:
        """ Check each file in dups and groping it. """
        for info in self._scan_path():
            if info.md5 in self.scanned_info:
                self.scanned_info[info.md5].append(info)
                logging.info('dup is found %s' % info)
            else:
                self.scanned_info[info.md5] = [info]

    def _scan_path(self) -> Iterable[FileInfo]:
        """ Walk by all files in target directory """
        for root, _, files in walk(self.dir_path):
            for name in (join(root, f) for f in files):
                if not isfile(name):
                    continue
                if getsize(name) < self.min_size:
                    continue
                yield FileInfo(name)
        return

    def get_dups(self) -> List[List[FileInfo]]:
        """Return dups from scanned_info"""
        deep = {}  # type: Dict[str, List[FileInfo]]
        for dups in (s for s in self.scanned_info.values() if len(s) > 1):
            for dup in dups:
                logging.info('for %s' % dup.path)
                md5_ = calc_md5(dup.path, True)
                if md5_ in deep:
                    deep[md5_].append(dup)
                else:
                    deep[md5_] = [dup]
        return [v for v in deep.values() if len(v) > 1]

    def __repr__(self) -> str:
        return "{} {}".format(self.dir_path, self.scanned_info)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='path to scan directory', default='/tmp')
    parser.add_argument('--log', help='log level', default='INFO')
    parser.add_argument('--ignore', help='ignore small files, less than 128KiB', action='store_true')
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=numeric_level)

    scanned = DirectoryScanner(args.path, args.ignore)
    scanned.traverse()
    result = scanned.get_dups()
    result.sort(key=lambda x: x[0].path)
    for dup in result:  # type: List[FileInfo]
        print(dup[0].md5)
        for i in dup:
            print("---   ", i.path)


if __name__ == "__main__":
    main()
