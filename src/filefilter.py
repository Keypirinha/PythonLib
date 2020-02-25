#
# Keypirinha: a fast launcher for Windows (keypirinha.com)
# Copyright 2013-2018 Jean-Charles Lefebvre <polyvertex@gmail.com>
#

import fnmatch
import glob
import os
import re
import stat
import sys

__all__ = ['create_filter']

PY36 = sys.version_info >= (3, 6)
IS_WINDOWS = os.name == 'nt'

EXPRESSION_REGEX = re.compile(
    r"""
        ^\s*
        (?:([+-])\s+)?
        (?:\:?([a-z_\:]{2,})\:\s+)?
        (.+)
        (?<!\s)\s*$
    """, flags=re.VERBOSE)

if IS_WINDOWS:
    import ctypes
    from collections import OrderedDict

    WIN_FILE_ATTRIBUTE = OrderedDict((
        ('directory', stat.FILE_ATTRIBUTE_DIRECTORY),
        ('dir', stat.FILE_ATTRIBUTE_DIRECTORY),

        ('hidden', stat.FILE_ATTRIBUTE_HIDDEN),

        ('symlink', stat.FILE_ATTRIBUTE_REPARSE_POINT),
        ('reparse_point', stat.FILE_ATTRIBUTE_REPARSE_POINT),

        ('compressed', stat.FILE_ATTRIBUTE_COMPRESSED),
        ('comp', stat.FILE_ATTRIBUTE_COMPRESSED),

        ('archive', stat.FILE_ATTRIBUTE_ARCHIVE),
        ('arch', stat.FILE_ATTRIBUTE_ARCHIVE),
        ('arc', stat.FILE_ATTRIBUTE_ARCHIVE),

        #('device', stat.FILE_ATTRIBUTE_DEVICE),
        #('dev', stat.FILE_ATTRIBUTE_DEVICE),

        ('encrypted', stat.FILE_ATTRIBUTE_ENCRYPTED),

        ('readonly', stat.FILE_ATTRIBUTE_READONLY),
        ('ro', stat.FILE_ATTRIBUTE_READONLY),

        ('system', stat.FILE_ATTRIBUTE_SYSTEM),
        ('sys', stat.FILE_ATTRIBUTE_SYSTEM)))


class Filter:
    def __init__(self, inclusive):
        self.hash_cache = None
        self.inclusive = inclusive

    def match(self, path):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError

    @classmethod
    def norm_path(cls, path, ispattern=False):
        # Notes on os.path.normpath():
        # * supports os.PathLike objects
        # * also removes trailing sep(s)
        path = os.path.normpath(path)

        if isinstance(path, bytes):
            path = os.fsdecode(path)
        assert isinstance(path, str)

        if ispattern:
            drive, path = os.path.splitdrive(path)
            if drive or os.path.isabs(path):
                raise ValueError('absolute path in filter')
            if not path:
                raise ValueError('invalid path format')

        return path

    @classmethod
    def norm_case(cls, s):
        # os.path.normcase() is a no-op on unix platforms
        return os.path.normcase(s) if IS_WINDOWS else s.lower()

class _PathFilter_Base(Filter):
    def __init__(self, pattern, case_sensitive, inclusive):
        super().__init__(inclusive)
        self.pattern = pattern # kept for __eq__, __str__ and match()
        self.case_sensitive = case_sensitive

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return NotImplemented

    def match(self, path):
        """
        Return a boolean that indicates if the given *path* matches the pattern
        of this filter.

        *path* can be a `str`, `bytes` or a path-like object.
        """
        raise NotImplementedError

class PathRegexFilter(_PathFilter_Base):
    def __init__(self, pattern, case_sensitive, nodrive, inclusive):
        super().__init__(pattern, case_sensitive, inclusive)
        self.nodrive = nodrive
        try:
            flags = 0
            if not case_sensitive:
                flags |= re.IGNORECASE
            self.matcher = re.compile(pattern, flags=flags).match
        except Exception as exc:
            raise ValueError('invalid regex: {}'.format(exc))

    def __hash__(self):
        # CAUTION: for this to be consistent, object must be immutable
        if self.hash_cache is None:
            self.hash_cache = hash((self.__class__.name,
                                    self.inclusive,
                                    self.case_sensitive,
                                    self.pattern,
                                    self.nodrive))
        return self.hash_cache

    def __str__(self):
        sign = '+ ' if self.inclusive else '- '

        props = 'regex:'
        if self.case_sensitive:
            props += 'case:'
        if self.nodrive:
            props += 'nodrive:'
        props += ' '

        return sign + props + self.pattern

    def match(self, path):
        path = self.norm_path(path, ispattern=False)

        if self.nodrive:
            path = os.path.splitdrive(path)[1]
            if not path:
                return False
            if path[0] != os.sep:
                path = os.sep + path

        if not path:
            return False

        if not self.case_sensitive:
            path = self.norm_case(path)

        return bool(self.matcher(path))

class PathTailFilter(_PathFilter_Base):
    def __init__(self, pattern, case_sensitive, inclusive):
        pattern = self.norm_path(pattern, ispattern=True)
        assert not glob.has_magic(pattern)

        if not case_sensitive:
            pattern = self.norm_case(pattern)

        # Ensure we match the full name of the first part to match in the path
        if pattern[0] != os.sep:
            pattern = os.sep + pattern

        super().__init__(pattern, case_sensitive, inclusive)
        self.seps_count = self.pattern.count(os.sep)

    def __hash__(self):
        # CAUTION: for this to be consistent, object must be immutable
        if self.hash_cache is None:
            self.hash_cache = hash((self.__class__.__name__,
                                    self.inclusive,
                                    self.case_sensitive,
                                    self.pattern,
                                    self.seps_count))
        return self.hash_cache

    def __str__(self):
        s = '+ ' if self.inclusive else '- '
        if self.case_sensitive:
            s += 'case: '
        return s + self.pattern

    def match(self, path):
        path = self.norm_path(path, ispattern=False)

        if self.seps_count == 0 or self.seps_count == 1:
            path = os.path.basename(path)

            if not self.case_sensitive:
                path = self.norm_case(path)

            # Stay consistent with __init__
            path = os.sep + path
        else:
            # lstrip the path so we match only its tail
            pos = len(path)
            for idx in range(self.seps_count):
                pos = path.rindex(os.sep, 0, pos - 1)
            if pos > 0:
                path = path[pos:] # keep the front sep

            if not self.case_sensitive:
                path = self.norm_case(path)

            # Stay consistent with __init__
            if path[0] != os.sep:
                path = os.sep + path

        delta = len(path) - len(self.pattern)
        if delta > 0:
            return path.endswith(self.pattern)
        elif delta == 0:
            return path == self.pattern
        else:
            return False

class PathShellFilter(_PathFilter_Base):
    def __init__(self, pattern, case_sensitive, nodrive, inclusive):
        pattern = self.norm_path(pattern, ispattern=True)
        assert glob.has_magic(pattern)
        if not case_sensitive:
            pattern = self.norm_case(pattern)

        super().__init__(pattern, case_sensitive, inclusive)

        self.patmatch = re.compile(fnmatch.translate(pattern)).match
        self.nodrive = nodrive

    def __hash__(self):
        # CAUTION: for this to be consistent, object must be immutable
        if self.hash_cache is None:
            self.hash_cache = hash((self.__class__.__name__,
                                    self.inclusive,
                                    self.case_sensitive,
                                    self.pattern,
                                    self.nodrive))
        return self.hash_cache

    def __str__(self):
        sign = '+ ' if self.inclusive else '- '

        props = ''
        if self.case_sensitive:
            props += 'case:'
        if self.nodrive:
            props += 'nodrive:'
        if props:
            props += ' '

        return sign + props + self.pattern

    def match(self, path):
        path = self.norm_path(path, ispattern=False)
        if not self.case_sensitive:
            path = self.norm_case(path)

        return bool(self.patmatch(path))

class ExtensionsFilter(Filter):
    def __init__(self, pattern, case_sensitive, inclusive):
        super().__init__(inclusive)

        if not case_sensitive:
            pattern = self.norm_case(pattern)

        if os.sep in pattern:
            raise ValueError('invalid or empty ext filter')

        self.case_sensitive = case_sensitive
        self.ext = frozenset(filter(None, re.split(r'[\s\;]+', pattern)))

    def __hash__(self):
        # CAUTION: for this to be consistent, object must be immutable
        if self.hash_cache is None:
            self.hash_cache = hash((self.inclusive, self.ext))
        return self.hash_cache

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return NotImplemented

    def __str__(self):
        sign = '+ ' if self.inclusive else '- '

        props = 'ext:'
        if self.case_sensitive:
            props += 'case:'
        props += ' '

        return sign + props + ' '.join(self.ext)

    def match(self, path_or_entry):
        if not self.ext:
            return False

        # Assume first that *path_or_entry* is `globex.GlobExEntry` object or
        # any other `os.DirEntry`-compatible
        try:
            basename = path_or_entry.name
        except AttributeError:
            basename = os.path.basename(path_or_entry) # os.PathLike supported

        if isinstance(basename, bytes):
            basename = os.fsdecode(basename)

        if not self.case_sensitive:
            basename = self.norm_case(basename)

        for ext in self.ext:
            if len(basename) > len(ext) and basename.endswith(ext):
                return True

        return False

if IS_WINDOWS:
    class WinAttrFilter(Filter):
        def __init__(self, pattern, match_all, inclusive):
            super().__init__(inclusive)

            self.match_all = match_all
            self.desired_attr = 0
            self.not_desired_attr = 0

            pattern = pattern.lower().split()
            for attr_str in pattern:
                if attr_str:
                    desired = True
                    if attr_str[0] == '!':
                        desired = False
                        attr_str = attr_str.lstrip('!')

                    try:
                        attr_flag = WIN_FILE_ATTRIBUTE[attr_str]
                    except KeyError:
                        raise ValueError('unknown file attribute "{}"'.format(
                            attr_str))

                    if desired:
                        self.desired_attr |= attr_flag
                    else:
                        self.not_desired_attr |= attr_flag

            if not self.desired_attr and not self.not_desired_attr:
                raise ValueError('empty attr or attr_all filter')

            if (self.desired_attr & self.not_desired_attr) != 0:
                raise ValueError(
                    'colliding attribute(s) found in attr or attr_all filter')

        def __hash__(self):
            # CAUTION: for this to be consistent, object must be immutable
            if self.hash_cache is None:
                self.hash_cache = hash((self.inclusive,
                                        self.match_all,
                                        self.desired_attr,
                                        self.not_desired_attr))
            return self.hash_cache

        def __eq__(self, other):
            if isinstance(other, self.__class__):
                return hash(self) == hash(other)
            return NotImplemented

        def __str__(self):
            s = '+ ' if self.inclusive else '- '
            s += 'attr_all:' if self.match_all else 'attr:'

            desired_attr = self.desired_attr
            not_desired_attr = self.not_desired_attr
            for attr_name, attr_flag in WIN_FILE_ATTRIBUTE.items():
                if desired_attr & attr_flag:
                    s += ' ' + attr_name
                    desired_attr &= ~attr_flag
                elif not_desired_attr & attr_flag:
                    s += ' !' + attr_name
                    not_desired_attr &= ~attr_flag

            return s

        def match(self, path_or_entry):
            # Assume first that *path_or_entry* is `globex.GlobExEntry` object
            # or any other `os.DirEntry`-compatible
            try:
                file_attr = path_or_entry.stat(
                    follow_symlinks=False).st_file_attributes
                path_or_entry = path_or_entry.path
            except OSError:
                return None
            except Exception:
                # AttributeError, TypeError, ... We are really blind here
                if PY36:
                    path_or_entry = os.fspath(path_or_entry)
                if isinstance(path_or_entry, bytes):
                    path_or_entry = os.fsdecode(path_or_entry)
                file_attr = ctypes.windll.kernel32.GetFileAttributesW(
                    path_or_entry)
                if file_attr == 0xffffffff: # INVALID_FILE_ATTRIBUTES
                    return None

            assert isinstance(path_or_entry, (str, bytes))

            # A file is considered *hidden* if it has the *hidden* attribute or
            # if its name starts with a '.' character.
            if not (file_attr & stat.FILE_ATTRIBUTE_HIDDEN):
                if isinstance(path_or_entry, bytes):
                    if path_or_entry[0] == b'.'[0]:
                        file_attr |= stat.FILE_ATTRIBUTE_HIDDEN
                elif path_or_entry[0] == '.':
                    file_attr |= stat.FILE_ATTRIBUTE_HIDDEN

            match = file_attr & self.desired_attr
            not_match = file_attr & self.not_desired_attr

            if self.match_all:
                return match == self.desired_attr and not_match == 0
            else:
                return match or (self.not_desired_attr != 0 and
                                 not_match != self.not_desired_attr)

def create_filter(expression):
    rem = EXPRESSION_REGEX.match(expression)
    if not rem:
        raise ValueError('invalid filter expression')

    inclusive = False if rem.group(1) == '-' else True
    props = rem.group(2)
    if not props:
        props_orig = ()
        props = ()
    else:
        props_orig = props[:]
        props = props.lower().split(':')
    pattern = rem.group(3)
    is_regex = False
    is_attr_or = False
    is_attr_and = False
    is_ext = False
    is_nodrive = False
    is_case_sensitive = False

    assert pattern == pattern.strip()

    for prop in props:
        if not prop:
            pass
        elif prop in ('re', 'regex'):
            is_regex = True
        elif prop == 'attr':
            is_attr_or = True
        elif prop == 'attr_all':
            is_attr_and = True
        elif prop == 'case':
            is_case_sensitive = True
        elif prop == 'ext':
            is_ext = True
        elif prop == 'nodrive':
            is_nodrive = True
        else:
            raise ValueError('invalid property "{}"'.format(prop))

    if sum((is_regex, is_attr_or, is_attr_and, is_ext)) > 1:
        raise ValueError('invalid mix of filter properties "{}"'.format(
                         props_orig))

    if is_ext:
        return ExtensionsFilter(pattern,
                                case_sensitive=is_case_sensitive,
                                inclusive=inclusive)
    elif is_attr_or or is_attr_and:
        if IS_WINDOWS:
            return WinAttrFilter(pattern,
                                 match_all=is_attr_and,
                                 inclusive=inclusive)
        else:
            raise NotImplementedError  # TODO
    elif is_regex:
        return PathRegexFilter(pattern,
                               case_sensitive=is_case_sensitive,
                               nodrive=is_nodrive,
                               inclusive=inclusive)
    else:
        tail = os.path.splitdrive(pattern)[1]
        if tail and glob.has_magic(tail):
            return PathShellFilter(pattern,
                                   case_sensitive=is_case_sensitive,
                                   nodrive=is_nodrive,
                                   inclusive=inclusive)
        else:
            # Note: PathTailFilter is "nodrive" by design
            return PathTailFilter(pattern,
                                  case_sensitive=is_case_sensitive,
                                  inclusive=inclusive)

if __name__ == '__main__':
    # Keep this __debug__ test constant so it can be stripped by the compiler in
    # non-debug mode
    if __debug__:
        print('DEBUG mode', flush=True)

        pf = create_filter('test')
        assert isinstance(pf, PathTailFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert pf.match('test')
        assert pf.match('TeSt')
        assert pf.match('/test')
        assert pf.match('/test/')
        assert pf.match(r'c:\test')
        assert pf.match('c:/test/')
        assert pf.match('D:/test')
        assert pf.match('testt') == False

        pf = create_filter('dir/test')
        assert isinstance(pf, PathTailFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert pf.match(r'c:\foo\dir\test\\')
        assert pf.match(r'c:\foo\_dir\test') == False

        # absolute path filters are not supported
        for s in ('/test', 'c:/test', r'\\?\c:\test', r'\\server\share\dir'):
            try:
                pf = create_filter(s)
                assert isinstance(pf, PathTailFilter)
            except ValueError as exc:
                assert 'absolute' in str(exc)
                continue # ok
            assert 0 # we should never get here

        pf = create_filter('t?st')
        assert isinstance(pf, PathShellFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match('test')
        assert pf.match('c:/dir/test') == False
        assert pf.match('dir/test') == False
        assert pf.match('tst') == False

        pf = create_filter('*/dir/t?st')
        assert isinstance(pf, PathShellFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match(r'c:\foo\dir\test')
        assert pf.match(r'c:\foo\dir\test\\')
        assert pf.match('dir/test') == False
        assert pf.match(r'c:\foo\_dir\test') == False
        assert pf.match('dir') == False
        assert pf.match('test') == False

        pf = create_filter('dir/*')
        assert isinstance(pf, PathShellFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match('dir/test')
        assert pf.match(r'\dir\test') == False
        assert pf.match(r'c:\foo\dir\test') == False
        assert pf.match(r'c:\foo\_dir\test') == False
        assert pf.match('dir') == False
        assert pf.match('test') == False

        pf = create_filter('*/dir/*')
        assert isinstance(pf, PathShellFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match('dir/test') == False
        assert pf.match('\\dir\\test')
        assert pf.match(r'any\dir\test')
        assert pf.match(r'any\dir') == False
        assert pf.match(r'c:\foo\dir\test')
        assert pf.match(r'c:\foo\dir\test\\')
        assert pf.match(r'test\any_dir\test') == False
        assert pf.match('dir') == False
        assert pf.match('test') == False

        pf = create_filter('regex: .*t.st.*')
        assert isinstance(pf, PathRegexFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match('test')
        assert pf.match('test world')
        assert pf.match('hello test')
        assert pf.match('hello test world')
        assert pf.match(r'c:\foo\dir\test')
        assert pf.match(r'c:\foo\dir\test\\')
        assert pf.match(r'c:\foo\test\bar')

        pf = create_filter('regex: .*t.st\\.doc')
        assert isinstance(pf, PathRegexFilter)
        assert pf.inclusive
        assert not pf.case_sensitive
        assert not pf.nodrive
        assert pf.match('test') == False
        assert pf.match('test.doc')
        assert pf.match('tEst.doc')
        assert pf.match('tOst.doc')
        assert pf.match('hello tost.doc')
