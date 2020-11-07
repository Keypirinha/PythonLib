#
# Keypirinha: a fast launcher for Windows (keypirinha.com)
# Copyright 2013-2018 Jean-Charles Lefebvre <polyvertex@gmail.com>
#

import keypirinha_api
import keypirinha as kp
import keypirinha_wintypes as kpwt
import sys
import enum
import ctypes
import io
import os
import stat
import sys
import traceback
import winreg
import urllib.parse
import chardet
import natsort

def raise_winerror(winerr=None, msg=None):
    """
    Raises :py:exc:`OSError` (formerly :py:exc:`WindowsError`) using the given
    Windows Error number. If the error number is not given,
    :py:func:`ctypes.GetLastError` is called.

    Does nothing if *winerr*, or by default, the result of
    :py:func:`ctypes.GetLastError`, is ``0`` (zero).
    """
    # ctypes.WinError could have been used but using OSError directly is more
    # obvious to the reader
    if winerr is None:
        winerr = ctypes.GetLastError()
    if msg is None:
        msg = ctypes.FormatError(winerr)
    if winerr:
        raise OSError(0, msg, None, winerr)

def fuzzy_score(search, against, apply_same_case_bonus=False):
    """
    Returns the matching score of a *search* string *against* another one.

    If case matters, the *apply_same_case_bonus* argument can be set to ``True``
    to apply a bonus on a matching characters that have the same case. You
    usually do not want this though since it might feel quite unnatural to the
    end-user.

    Returns:
        int: The score is an unsigned integer. ``0`` (zero) means no match, a
        value greater than zero means a match. The higher the score, the better
        the match is.
    """
    return keypirinha_api.fuzzy_score(search, against, apply_same_case_bonus)

def kwargs_encode(**kwargs):
    """
    URL encodes passed keyword arguments into an escaped string that can be used
    as a *target* property for a :py:class:`keypirinha.CatalogItem` object.

    Only basic types are allowed: ``bool``, ``int``, ``float`` and ``str``.
    **Hint:** use the unpack operator to pass a dictionary like in:
    ``kwargs_encode(**mydict)``

    Returns:
        str: The encoded string that can be decoded by :py:func:`kwargs_decode`.

    Raises:
        TypeError: The type of a passed value is invalid.
        UnicodeEncodeError: :py:func:`urllib.parse.quote_plus` failed.

    See Also:
        :py:func:`kwargs_decode`
    """
    # sorted() is critical here in order to get consistent unit target strings!
    # we might get doubles in the resulting catalog otherwise
    quoted = []
    for k in sorted(kwargs):
        val = kwargs[k]
        if not isinstance(val, (bool, int, float, str)):
            raise TypeError('type not supported for argument named ' + k)
        quoted.append('{}={}'.format(
            urllib.parse.quote_plus(k, encoding='utf-8', errors='strict'),
            urllib.parse.quote_plus(repr(val), encoding='utf-8', errors='strict')))
    return ' '.join(quoted)

def kwargs_decode(encoded_string):
    """
    Decodes a string encoded by :py:func:`kwargs_encode` and returns a
    dictionary.

    See Also:
        :py:func:`kwargs_encode`
    """
    decoded = {}
    for pair in iter(encoded_string.split()):
        k, v = (urllib.parse.unquote_plus(x) for x in pair.split('=', 1))
        decoded[k] = eval(v)
    return decoded

def get_clipboard():
    """
    Returns a string containing system's clipboard only if it contains text.

    An empty string is returned otherwise.

    See Also:
        :py:func:`set_clipboard`
    """
    return keypirinha_api.get_clipboard()

def set_clipboard(text):
    """
    Sets the content of system's clipboard.

    See Also:
        :py:func:`get_clipboard`
    """
    return keypirinha_api.set_clipboard(text)

def cmdline_split(cmdline):
    """
    Splits and unquotes (the Windows way) the given command line (string).

    Returns:
        list: The split command line, a list of strings containing every
        argument.

    Raises:
        OSError: The underlying call to Win32's ``CommandLineToArgvW`` function
            failed.

    See Also:
        :py:func:`cmdline_quote` if you want to do the opposite (i.e.: to join
        and quote a list of arguments).
    """
    return keypirinha_api.cmdline_split(cmdline)

def cmdline_quote(arg_or_list, force_quote=False):
    """
    Joins and quotes arguments the Windows way.

    Args:
        arg_or_list (list): The list of arguments (strings) to join and quote.
            This arguments can also be a string, in which case it is handled as
            if it was a list with a single element.
        force_quote (bool): Force every arguments, even those that normally
            would not require to be quoted (i.e.: the ones with no white space
            included).

    Returns:
        str: The resulting string (command line) containing the quoted
        arguments.

    Raises:
        TypeError: At least one of the passed arguments has an unsupported type.

    See Also:
        :py:func:`cmdline_split` if you want to do the opposite (i.e.: to split
        a command line).
    """
    if isinstance(arg_or_list, str):
        arg_or_list = [arg_or_list]
    elif isinstance(arg_or_list, tuple):
        arg_or_list = list(arg_or_list)
    elif not isinstance(arg_or_list, list):
        raise TypeError('invalid args type')
    return keypirinha_api.cmdline_quote(arg_or_list, force_quote)

@enum.unique
class FileAttr(enum.IntEnum):
    """File attribute flags returned by :py:func:`file_attributes`."""
    #: Path points to an existing item of an unknown type.
    #: This flag might be combined with other flags except :py:const:`DIR`,
    #: :py:const:`FILE`, :py:const:`LINK`, :py:const:`EXE`,
    #: :py:const:`EXE_CONSOLE` and :py:const:`EXE_GUI`.
    UNKNOWN_TYPE = 0x000001

    #: Path points to a directory.
    DIR = 0x000002

    #: Path points to a regular file.
    FILE = 0x000004

    #: Path points to a link file (``.lnk``).
    LINK = 0x000008

    #: Path points to an executable.
    #: Combined with :py:const:`FILE`.
    EXE = 0x000010

    #: Path points to an executable.
    #: Combined with :py:const:`FILE` and :py:const:`EXE`.
    EXE_CONSOLE = 0x000020

    #: Path points to an executable.
    #: Combined with :py:const:`FILE` and :py:const:`EXE`.
    EXE_GUI = 0x000040

    #: File is read-only.
    READONLY = 0x020000

    #: File is hidden.
    HIDDEN = 0x040000

    #: File is compressed.
    COMPRESSED = 0x080000

    #: File is encrypted.
    ENCRYPTED = 0x100000

    #: File is shared.
    SHARED = 0x200000

    #: File is a removable media **or** is stored on a removable media.
    REMOVABLE = 0x400000

def file_attributes(file, follow_link=False):
    """
    Fetches and returns the attributes of a given *file*.

    If the *follow_link* argument is True and *file* is a link, the
    function will return the attributes of its target; even if the target is
    also a link file (i.e.: only one level of recursion).

    Returns:
        FileAttr: Combination of attributes.

    Raises:
        FileNotFoundError: *file* is not found or not accessible. Or if the link
            could not be resolved (in case *follow_link* is True).
    """
    attr = keypirinha_api.file_attributes(file, follow_link)
    if not attr:
        raise FileNotFoundError("file not found: {}".format(file))
    return attr

def chardet_open(file, mode="r", buffering=-1, encoding=None, **kwargs):
    """
    An :py:func:`open` function that **tries** to detect text file's encoding.

    This function has the same return value, behavior and parameters than the
    standard :py:func:`open` function except that ``encoding`` argument is
    ignored. It may raise the same exceptions as well.

    Note:
        * Automatic encoding detection is skipped if the ``b`` flag is specified
          in the ``mode`` argument.
        * The ``chardet`` module is used for the auto-detection.
    """
    if ("file" in kwargs or "mode" in kwargs or "buffering" in kwargs or
            "encoding" in kwargs):
        raise ValueError("kwargs")

    if "b" in mode:
        return open(file, mode, buffering, encoding, **kwargs)
    elif (mode in ("r", "rt", "tr") and
            os.path.getsize(file) <= 50 * 1024 * 1024):
        # If the file is small enough (arbitrary size), blindly try to decode it
        # as utf-8 since many users reported chardet does not detect it well.
        # See: https://github.com/Keypirinha/Keypirinha/issues/336
        content = ""
        try:
            with open(file, mode="rt",
                      encoding="utf-8", errors="strict") as fin:
                content = fin.read()
        except ValueError:  # UnicodeError
            pass
        else:
            return io.StringIO(content)
    else:
        # try to detect file's encoding
        detector = chardet.UniversalDetector()
        with open(file, mode="rb") as fin:
            while True:
                line = fin.readline(8 * 1024)
                if len(line) == 0:
                    break  # eof
                detector.feed(line)
                if detector.done:
                    break
        detector.close()

        return open(file, mode, buffering, detector.result['encoding'],
                    **kwargs)

def chardet_slurp(file):
    """
    Fully extract a text file into memory after having automatically detected
    its encoding.
    """
    with open(file, mode="rb") as fin:
        raw = fin.read()

    # blindly try to decode as utf-8 since many users reported chardet does not
    # detect it well
    # see: https://github.com/Keypirinha/Keypirinha/issues/336
    try:
        return raw.decode(encoding="utf-8", errors="strict")
    except UnicodeError:
        pass

    # use chardet to detect encoding
    res = chardet.detect(raw)
    return raw.decode(encoding=res['encoding'], errors="strict")

def read_link(link_file):
    """
    Reads the properties of a Shell Link File (``.lnk``).

    Args:
        link_file (str): The path of the ``.lnk`` file.

    Returns:
        dict: A dict containing the properties:
        ::
            {'target': "The resolved target file; path is already expanded",
                'params': "Target's parameters (may be None)",
                'expanded_params_list': ["split", "and", "expanded 'params'", "or empty list"],
                'working_dir': "Working directory (may be None)",
                'desc': "Description (may be None)",
                'show_cmd': "The 'show command' value (int; can be SW_SHOWNORMAL, SW_SHOWMAXIMIZED or SW_SHOWMINIMIZED; may be None)",
                'icon_location': "The icon location string that should be readable by shell_string_resource() (may be None)",
                'runas': "A boolean to indicate target should be run with elevated privileges",
                'flags': "The raw flags value read from IShellLink (int)",
                'is_msi': "A boolean flag equivalent to the (flags & SLDF_HAS_DARWINID) test"}

    Raises:
        IOError: The file could not be read or is not a link.
    """
    link_info = keypirinha_api.read_link(link_file)
    if link_info is None:
        raise IOError("file not found or is not a link: " + link_file)
    if link_info['params'] is not None:
        link_info['expanded_params_list'] = [
            os.path.expandvars(a) for a in cmdline_split(link_info['params'])]
    else:
        link_info['expanded_params_list'] = []
    return link_info

@enum.unique
class ScanFlags(enum.IntEnum):
    """The *flags* to pass to :py:func:`scan_directory`."""
    FILES = 0x01           #: List files (i.e.: everything that is not a directory)
    DIRS = 0x02            #: List directories
    HIDDEN = 0x04          #: List hidden files
    CASE_SENSITIVE = 0x08  #: Case-sensitive scan (default is case-unsensitive)
    ABORT_ON_ERROR = 0x10  #: Abort if any error occurs while scanning a sub-folder
    DEFAULT = FILES | DIRS #: Combination of :py:const:`SCAN_FILES` | :py:const:`SCAN_DIRS`

def scan_directory(base_dir, name_patterns='*', flags=ScanFlags.DEFAULT, max_level=0):
    """
    Walks a directory and builds a list of relative paths.

    Warning:
        * This function is only kept to maintain backward compatibility. It is
          recommended to use :py:func:`os.scandir` instead.
        * This function has been developed as a fast alternative to
          :py:func:`os.walk`. However since then, :py:func:`os.scandir` has been
          implemented and offers a more Pythonic way to scan a directory.

    This function offers an alternative to :py:func:`os.walk` or the more recent
    :py:func:`os.scandir`, that has the ability to filter the elements to find
    by name and/or by type, and to define how deep the scan has to be done.

    Args:
        base_dir (str): The path to the directory to scan.
        name_patterns (list): Allows to apply one (a string can be passed) or
            several filters to the **name** of the found elements. Allowed
            wildcards are ``*`` (zero or several unknown characters) and ``?``
            (any character). If you only want to apply one filter, you may pass
            a string. Typical example: ``*.txt`` to list all the ``.txt`` files.
        flags (ScanFlags): One or a combination of flags to control scan's
            behavior.
        max_level (int): Specifies how deep the scan should be. ``0`` (zero)
            means only the immediate content of the specified *base_dir* will be
            returned. A *max_level* of ``1`` will also include the immediate
            content of its sub-directories, and so on... Specify a value of
            ``-1`` to walk the tree completely. The maximum theorical value is
            ``0xffffffff``. A negative value equals ``0xffffffff``.

    Returns:
        list: The paths (strings) of found files and/or directories. Paths are
        relative to *base_dir*. The full path of an element can be build that
        way:
        ::
            root_dir = "c:/dir"
            files = keypirinha.scan_directory(root_dir)
            if len(files) > 0:
                full_path = os.path.join(root_dir, files[0])

    Raises:
        OSError: something went wrong while trying to open the specified
            *base_dir* or during the scan.

    Note:
        Win32's ``FindFirstFile`` is used internally.

    .. deprecated::
        This function is deprecated in favor of :py:func:`os.scandir`. It is
        kept here only to maintain backward compatibility.
    """
    if isinstance(name_patterns, str):
        name_patterns = [name_patterns]
    if max_level < 0:
        max_level = 0xFFFFFFFF
    elif max_level > 0xFFFFFFFF:
        max_level = 0
    result = keypirinha_api.scan_directory(base_dir, name_patterns, flags, max_level)
    if isinstance(result, int):
        raise_winerror(
            result,
            'failed to scan directory "{}" (code {})'.format(base_dir, result))
    return result

def browse_directory(
        plugin, base_dir, check_base_dir=True,
        search_terms="", store_score=False,
        show_dirs_first=True, show_hidden_files=False, show_system_files=False):
    """
    Scan the first level of a directory according to a search term (optional)
    and some filtering rules in order to get :py:class:`keypirinha.CatalogItem`
    objects to feed :py:meth:`keypirinha.Plugin.set_suggestions`.

    Args:
        plugin (keypirinha.Plugin): The parent plugin of the
            :py:class:`keypirinha.CatalogItem` objects to be created. It may be
            used to print error/warning messages as well.
        base_dir (str): The path of the directory to browse.
        check_base_dir (bool): Print an error message if the directory does not
            exist and returns an :py:const:`keypirinha.ItemCategory.ERROR`
            :py:class:`keypirinha.CatalogItem` object in the result (the format
            of the returned ``tuple`` is unchanged).
        search_terms (str): If not empty, it will be *fuzzy matched* against the
            name of each found item (see :py:func:`fuzzy_score`). If the
            returned score is zero, the item is not included in the returned
            list. If the string is empty, items will be sorted by name using the
            ``natsort`` module.
        store_score (bool): If *search_terms* is not empty, the resulting score
            of the call to :py:func:`fuzzy_score` will be stored in the
            ``data_bag`` property of every inserted result item.
        show_dirs_first (bool): Indicates if directories should be pushed at
            the top of the resulting list.
        show_hidden_files (bool): Indicates if hidden items should included.
            Note that a hidden item can also be system.
        show_system_files (bool): Indicates if system items should included.
            Note that a system item can also be hidden.

    Returns:
        tuple: A tuple of 3 elements ``(items, match_method, sort_method)``
        where *items* is a list of :py:class:`keypirinha.CatalogItem` objects,
        *match_method* is a :py:class:`keypirinha.Match` value and *sort_method*
        is a :py:class:`keypirinha.Sort` value.
    """
    def _create_item(plugin, entry, win_attr, data_bag):
        return plugin.create_item(
            category=kp.ItemCategory.FILE,
            label=entry.name,
            short_desc="",
            target=entry.path,
            args_hint=kp.ItemArgsHint.ACCEPTED,
            hit_hint=kp.ItemHitHint.KEEPALL,
            loop_on_suggest=True,
            data_bag=data_bag)

    file_entries = {}
    dir_entries = {} if show_dirs_first else file_entries

    if len(search_terms) > 0:
        match_method = kp.Match.FUZZY
        sort_method = kp.Sort.SCORE_DESC
    else:
        match_method = kp.Match.ANY
        sort_method = kp.Sort.NONE

    if check_base_dir and not os.path.isdir(base_dir):
        plugin.err("Directory not found: " + base_dir)
        return (
            [plugin.create_error_item(
                label=search_terms,
                short_desc="Directory not found: " + base_dir)],
            match_method, sort_method)

    # browse directory
    max_score = None
    for entry in os.scandir(base_dir):
        entry_stat = entry.stat(follow_symlinks=False) # does not require a syscall when follow_symlinks is False on Windows
        entry_attr = entry_stat.st_file_attributes

        if entry_attr & stat.FILE_ATTRIBUTE_HIDDEN and not show_hidden_files:
            continue
        if entry_attr & stat.FILE_ATTRIBUTE_SYSTEM and not show_system_files:
            continue

        match_score = None
        if len(search_terms) > 0:
            match_score = keypirinha_api.fuzzy_score(search_terms, entry.name, False)
            if not match_score:
                continue
            if not max_score or match_score > max_score:
                max_score = match_score
            match_score = str(match_score) if store_score else None

        if entry_attr & stat.FILE_ATTRIBUTE_DIRECTORY:
            dir_entries[entry.name] = (entry, entry_attr, match_score)
        else:
            file_entries[entry.name] = (entry, entry_attr, match_score)

    # sort entries and build the suggestions list
    suggestions = []
    sort_alg = natsort.ns.PATH | natsort.ns.LOCALE | natsort.ns.IGNORECASE
    if show_dirs_first:
        for entry_name in natsort.natsorted(dir_entries.keys(), alg=sort_alg):
            suggestions.append(_create_item(plugin,
                                            dir_entries[entry_name][0],
                                            dir_entries[entry_name][1],
                                            dir_entries[entry_name][2]))
    for entry_name in natsort.natsorted(file_entries.keys(), alg=sort_alg):
        suggestions.append(_create_item(plugin,
                                        file_entries[entry_name][0],
                                        file_entries[entry_name][1],
                                        file_entries[entry_name][2]))

    # prepend the "." item if needed
    if not len(search_terms) and (
            match_method == kp.Match.ANY and sort_method == kp.Sort.NONE):
        suggestions.insert(0, plugin.create_item(
            category=kp.ItemCategory.FILE,
            label=".",
            short_desc="",
            target=base_dir,
            args_hint=kp.ItemArgsHint.ACCEPTED,
            hit_hint=kp.ItemHitHint.KEEPALL,
            loop_on_suggest=True,
            data_bag=None if max_score is None else str(max_score + 1)))

    return suggestions, match_method, sort_method

def shell_execute(
        thing, args="", working_dir="", verb="", try_runas=True,
        detect_nongui=True, api_flags=None, terminal_cmd=None, show=-1):
    """
    Executes, opens, edits (or whatever) an application, a file, a directory, by
    calling Win32's ``ShellExecuteEx`` function.

    Args:
        thing (str): The *thing* to execute/launch/edit/whatever. It can be a
            file, a directory, or anything recognized by ``ShellExecuteEx``.
        args (str): The **quoted** arguments (optional). Note that a
            :py:class:`list` of arguments (strings) can be given in which case
            :py:func:`cmdline_quote` is implicitely called.
        working_dir (str): The directory to execute from. This value can be
            empty, in which case this function tries to automatically detect it.
        verb (str): Specifies the action to be performed and is passed as-is to
            ``ShellExecuteEx``. This value can be empty to request default
            action associated with the given *thing*. Here is the list of the
            common verbs from the Microsoft's documentation: ``open``, ``edit``,
            ``explore``, ``find``, ``print`` and ``properties``.
            Note that all *verb* are not available with all kind of *thing*.
        try_runas (bool): Automatically try to run with elevated permissions if
            the first call to ``ShellExecuteEx`` failed with ``ACCESS_DENIED``
            error.
        detect_nongui (bool): Automatically detect if *thing* is a console
            application (or a link pointing to a console application). In that
            case, the ``terminal`` setting of the ``external`` section defined
            in the application's configuration file will be used to launch
            *thing*.
        api_flags (int): If specified, those flags will be forwarded to
            ``ShellExecuteEx``. The ``SEE_MASK_NOASYNC`` (``0x100``),
            ``SEE_MASK_FLAG_NO_UI`` (``0x400``) and ``SEE_MASK_INVOKEIDLIST``
            (``0xC``) flags are passed if this argument is ``None``.
            See ``ShellExecuteEx`` documentation from Microsoft for more info.
        terminal_cmd (str): If *detect_nongui* is ``True``, this value allows to
            force the console emulator to use, instead of reading the
            ``terminal`` setting of the ``external`` section defined in the
            application's configuration file. Note that, like for the *args*
            parameter, a :py:class:`list` of arguments (strings) can be given in
            which case :py:func:`cmdline_quote` is implicitely called.
        show (int): Value directly forwarded to the ``nShow`` parameter of
            ``ShellExecuteEx``. It must be one of the ``SW_`` constants. If this
            value is less than zero, default will be applied (currently
            ``SW_SHOWNORMAL``).

    Raises:
        FileNotFoundError: The *thing* was not found.
        OSError: Specified *thing* is a link that could not be read. Or
            ``ShellExecuteEx`` failed with the given thing and arguments. Or an
            unexpected/unknown error occurred internally.

    Warning:
        It is highly recommended to use this function instead of the standard
        :py:func:`os.startfile` because the later internally calls the
        ``ShellExecute`` system function, which is obsolete, known to be bugged
        and behaves incorrectly in some cases.

    Note:
        * A successful call does not necessarily mean the item has effectively
          been launched/executed as expected, or that the launched process ended
          successfully.
        * This function tries to resolve shell links for the *thing* and the
          *terminal_cmd* arguments. Which also mean shortucts' arguments will be
          prepended, if any, to the final list of arguments.

    See Also:
        :py:func:`web_browser_command`, which is the preferred function to open
        a URL since it takes care of applying user's preferences.
    """
    if args is None:
        args = []
    elif isinstance(args, str):
        args = cmdline_split(args)
    elif isinstance(args, tuple):
        args = list(args)
    elif not isinstance(args, list):
        raise TypeError("Invalid args argument")
    if working_dir is None:
        working_dir = ""
    if verb is None:
        verb = ""

    initial_thing = thing

    # try to resolve thing in case caller wants to launch an executable
    # file_attributes(), which is called below, needs a path
    if "/" not in thing and "\\" not in thing:
        resolved_thing = shell_resolve_exe_path(thing)
        if resolved_thing is not None:
            thing = resolved_thing

    # if *thing* is a shell link, try to resolve it first and also get its
    # embedded arguments to prepend them to the caller's ones
    try:
        thing_attr = file_attributes(thing) # may raise FileNotFoundError
    except FileNotFoundError:
        thing_attr = None
    if thing_attr is not None and thing_attr & FileAttr.LINK:
        try:
            link_info = read_link(thing)
        except IOError:
            link_info = None

        # avoid any trouble, run away from MSI shortcuts
        if link_info and not link_info['is_msi']:
            # update the *thing* value and its file attributes
            thing = link_info['target']
            try:
                thing_attr = file_attributes(thing)
            except FileNotFoundError:
                thing_attr = None

            # prepend shortcut's arguments if any
            if link_info['expanded_params_list']:
                args[:0] = link_info['expanded_params_list']

            # use shortcut's workdir if we don't have any yet
            if (thing_attr is not None and not len(working_dir) and
                    link_info['working_dir'] is not None):
                working_dir = link_info['working_dir']

            # run with elevated privileges?
            if link_info['runas'] and verb in ("", "open"):
                verb = "runas"

    # use the base directory of *thing* if we don't have a workdir yet
    # we do that now since we don't want to use terminal_cmd's one
    if thing_attr is not None and not len(working_dir):
        working_dir = os.path.dirname(thing)

    # if *detect_nongui* is enabled and *thing* is a console exe/script, try to
    # use the given *terminal_cmd* argument, or by default, get application's
    # *terminal* setting ([external] section) in order to launch the *thing*.
    while (thing_attr is not None and thing_attr & FileAttr.EXE_CONSOLE and
            detect_nongui and (verb == "" or verb == "open" or verb == "runas")):
        if not terminal_cmd:
            terminal_cmd = kp.settings().get_stripped("terminal", "external", unquote=False)
        if not terminal_cmd:
            break

        if isinstance(terminal_cmd, str):
            terminal_cmd = cmdline_split(terminal_cmd)
        elif isinstance(terminal_cmd, tuple):
            terminal_cmd = list(terminal_cmd)

        # in case terminal_cmd[0] is a shortcut as well, resolve its target and
        # prepend its arguments
        try:
            attr = file_attributes(terminal_cmd[0])
        except FileNotFoundError:
            break
        if attr & FileAttr.LINK:
            try:
                link_info = read_link(terminal_cmd[0])
            except IOError:
                link_info = None

            # avoid any trouble, run away from MSI shortcuts
            if link_info and not link_info['is_msi']:
                terminal_cmd[0] = link_info['target']
                if link_info['expanded_params_list']:
                    terminal_cmd[1:0] = link_info['expanded_params_list']
                if link_info['runas'] and verb in ("", "open"): # run with elevated privileges?
                    verb = "runas"

        # apply the final terminal_cmd to *thing* and *args*
        args[:0] = terminal_cmd[1:] + [thing]
        thing = terminal_cmd[0]

        break

    args = cmdline_quote(args)

    while 1:
        res = keypirinha_api.shell_execute(
            thing, args, working_dir, verb, api_flags, show)
        if res == 0:
            return
        elif res in (2, 3): # ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND
            raise FileNotFoundError('file not found: "{}" (initial path: "{}")'.format(thing, initial_thing))
        elif res == 5 and try_runas and verb in ("", "open"): # ACCESS_DENIED
            verb = "runas"
            continue
        raise_winerror(res)

def shell_known_folder_path(guid):
    """
    Returns the path of a Shell Known Folder according to its GUID.

    Args:
        guid (str): The GUID of the desired Known Folder. Format must be:
            ``{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`` (case-insensitive; the
            curly braces can be omited). The list of Known Folders is available
            on `MSDN <https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457.aspx>`_.
            Note that not all Known Folders are available on every platforms.

    Raises:
        ValueError: The specified GUID is invalid (type, format or value). Or
            this Known Folder is not available on this platform. Or the
            specified Known Folder is virtual.
        OSError: The Known Folder is virtual, or not available on this platform.

    Note:
        Internally calls Win32's ``SHGetKnownFolderPath``.
    """
    return keypirinha_api.shell_known_folder_path(guid)

def shell_resolve_exe_path(path_or_name):
    """
    Tries to resolve *path_or_name* using environment ``PATH`` and ``PATHEXT``
    variables.

    *path_or_name* can be a path or just the name of the executable to
    find, in which case ``PATHEXT`` will be used to find a match in the
    directories listed in the ``PATH`` value.

    Returns ``None`` if executable could not be found or if an error occurred.
    """
    return keypirinha_api.shell_resolve_exe_path(path_or_name)

def shell_string_resource(resource_location):
    """
    Returns the content of a string resource from an external module (DLL)
    according to its location. Returns ``None`` if an error occurred.

    Args:
        resource_location (str): The location of the desired string. The
            expected format is normally "@<PE-path>,-<stringID>" but the
            underlying function tries to be as flexible as possible since a lot
            of applications and shell extensions do not strictly comply to
            Microsoft's rules.
    """
    return keypirinha_api.shell_string_resource(resource_location)

def shell_url_scheme_to_command(url_scheme):
    """
    Get system's default command line associated with the given URL scheme(s);
    and the location of its default icon.

    Args:
        url_scheme (str): The URL scheme name (e.g. "http", "ftp", "mailto",
            "skype", ...).
            This argument **can also be an iterable** of URL schemes, in which
            case this function iterates over the given schemes until it finds a
            valid associated command line.

    Returns:
        tuple: The command line associated with the scheme and the shell
        location string of class' default icon.

    See Also:
        :py:func:`cmdline_split`
    """
    if isinstance(url_scheme, str):
        url_scheme = [url_scheme]
    for proto in url_scheme:
        command, def_ico_loc = keypirinha_api.shell_url_scheme_to_command(proto)
        if command:
            return command, def_ico_loc
    return None, None

def web_browser_command(private_mode=None, new_window=None, url=None, execute=False):
    """
    A Swiss Knife function to deal with the web browser setup in Keypirinha's
    global configuration (see the ``web_browser`` setting in the ``[external]``
    section), or by default, with the system's default web browser.

    This function allows to:

    * Open the given URL
    * Get the split command line to execute the web browser, including the given
      URL
    * Get the split command line to execute the web browser, including a
      placeholder element to indicate where to insert the URL to open

    All the above cases take the *private_mode* and *new_window* arguments into
    account. The execution flow of this function depends on the *url* and
    *execute* arguments only.

    Args:
        private_mode (bool): Hint the browser you want to launch it in Private
            (or Incognito) mode. By default (i.e. ``None``), this function will
            get user's configuration, or will fall back to browser's default
            behavior. Specifying a boolean value (other than ``None``), will
            override user's configuration.
        new_window (bool):  Hint the browser you want to launch a new window. By
            default (i.e. ``None``), this function will get user's
            configuration, or will fall back to browser's default behavior.
            Specifying a boolean value (other than ``None``), will override
            user's configuration.
        url (str): If specified, the given URL(s) will be inserted at the right
            place in the command line so the caller does not have to do it
            manually. This is convenient since, while being uncommon, the URL(s)
            might have to be inserted in the command line instead of just being
            appended.

            .. tip::
                *url* can also be an iterable of strings in case several URLs
                are to be launched, in which case, they will be opened together
                if possible (i.e. using the same command line).
        execute (bool): Only taken into account if a *url* is specified. If this
            argument is ``True``, the given *url* will be opened using
            :py:func:`shell_execute` and taking the *private_mode* and
            *new_window* arguments into account if possible. The return value is
            then a boolean, indicating whether or not the URL has been launched
            successfully.

    Returns:
        list
            If *execute* is ``False``, returns a list of arguments that
            represent the command line to execute in order to launch the web web
            browser. In that case, *url* can be specified so the returned
            command line arguments list is ready to use. Otherwise, the returned
            list will contain a placeholder (``%1``) to indicate where to insert
            the URL to open. Returns ``None`` if no browser could be found.

        bool
            If *execute* is ``True`` and a *url* is specified, this function
            will try to open the URL and returns a boolean to indicate whether
            or not the launch request is successful.

    Raises:
        TypeError: The given *url* argument is invalid.
    """
    def _insertopt(args, opt):
        if opt not in args:
            try:
                idxddash = args.index("--")
            except ValueError:
                idxddash = len(args)
            try:
                idxph = args.index("%1")
            except ValueError:
                idxph = len(args)
            args.insert(min(idxddash, idxph), opt)
        return args

    def _inserturls(args, urls):
        if isinstance(urls, str):
            urls = [urls] if len(urls.strip()) else []
        if urls:
            while urls.count("%1") > 1:
                urls.remove("%1")
            try:
                idx = args.index("%1")
                args.remove("%1")
            except ValueError:
                idx = len(args)
            for single_url in urls:
                if single_url not in args: # avoid duplicating "%1" for example (very defensive code)
                    args.insert(idx, single_url)
                    idx += 1
        return args

    def _launch(thing):
        try:
            if isinstance(thing, (list, tuple)):
                shell_execute(thing[0], args=thing[1:])
            elif isinstance(thing, str):
                shell_execute(thing)
            else:
                raise TypeError("invalid argument")
            return True
        except (FileNotFoundError, OSError) as exc:
            print("Failed to open URL(s). Error: {}. Argument: {}".format(str(exc), thing),
                file=sys.stderr)
        return False

    if url is None:
        url = []
    elif isinstance(url, str):
        url = [url] if len(url.strip()) else []
    elif not isinstance(url, list):
        url = list(url)

    if len(url) > 1 and not execute:
        raise ValueError("'execute' option must be enabled when several URLs are specified")

    # Get the command line of the configured web browser, or by default, the
    # system's default web browser. Keypirinha took care of setting up the
    # web_browser value in case the user left it empty.
    command = kp.settings().get_stripped("web_browser", "external", unquote=False)
    if not command:
        command = shell_url_scheme_to_command(("http", "https"))[0]
    if not command:
        # We could not find the default web browser but the caller wants the URL
        # to be opened so, as a last chance, we try to blindly shell_execute it,
        # hoping the os will just deal with it.
        if url and execute:
            result = True
            for single_url in url:
                if not _launch(single_url):
                    result = False
            return result
        return None

    # Apply global preferences for the private_mode and new_window parameters in
    # case they haven't been forced by the caller
    if private_mode is None:
        private_mode = kp.settings().get_bool("web_browser_private_mode", "external", None)
    if new_window is None:
        new_window = kp.settings().get_bool("web_browser_new_window", "external", None)

    args = cmdline_split(command)
    arg0lc = os.path.normpath(os.path.normcase(args[0])).lower() # lower() is unnecessary on windows
    cmdlines = []

    # chrome and alikes
    if (arg0lc.endswith("chrome.exe") or
            arg0lc.endswith("googlechromeportable.exe") or
            arg0lc.endswith("vivaldi.exe") or
            arg0lc.endswith("iridium.exe")):
        final_args = args[:]  # copy

        # cleanup command line
        for unwanted_opt in ("--single-argument", "-single-argument", ):
            while unwanted_opt in final_args:
                final_args.remove(unwanted_opt)

        if private_mode:
            final_args = _insertopt(final_args, "--incognito")
        if new_window:
            final_args = _insertopt(final_args, "--new-window")

        if not url:
            final_args.append("%1")
        else:
            final_args = _inserturls(final_args, url)
        cmdlines.append(final_args)

    # firefox
    # * accepts either "-private-window URL" OR "-new-window URL"
    # * if one of them has been enabled, we must cleanup the command line since
    #   -osint or -url flag would collide otherwise
    # * -private-window and -new-window options are per-URL
    elif (arg0lc.endswith("firefox.exe") or
            arg0lc.endswith("firefoxportable.exe") or
            arg0lc.endswith("firefox-portable.exe") or
            arg0lc.endswith("palemoon.exe") or
            arg0lc.endswith("palemoonportable.exe") or
            arg0lc.endswith("palemoon-portable.exe") or
            arg0lc.endswith("waterfox.exe") or
            arg0lc.endswith("waterfoxportable.exe") or
            arg0lc.endswith("waterfox-portable.exe")):
        final_args = args[:]  # copy

        # cleanup command line
        for unwanted_opt in ("-osint", ):
            while unwanted_opt in final_args:
                final_args.remove(unwanted_opt)
        for unwanted_opt in ("-url", "-private-window", "-new-tab", "-new-window"):
            while unwanted_opt in final_args:
                idx = final_args.index(unwanted_opt)
                if len(final_args) >= idx + 2 and final_args[idx+1].startswith("-"):
                    # avoid to delete a next -option accidentally
                    # we have to check for that since the -private-window option
                    # for example, has two forms, with and without a URL argument
                    del final_args[idx:idx+1]
                else:
                    del final_args[idx:idx+2]

        if not url:
            url = ["%1"]
        first = True
        for single_url in url:
            if private_mode:
                final_args.append("-private-window")
            elif new_window:
                final_args.append("-new-window" if first else "-new-tab")
            else:
                final_args.append("-url")
            final_args.append(single_url)
            first = False

        cmdlines.append(final_args)

    # iexplorer
    # * one command line per URL
    elif arg0lc.endswith("iexplore.exe"):
        if not url:
            url = ["%1"]
        for single_url in url:
            final_args = args[:]  # copy
            if private_mode:
                final_args = _insertopt(final_args, "-private")
            if new_window:
                final_args = _insertopt(final_args, "-new") # obsolete as of ie7 (no extra arg necessary)
            final_args = _inserturls(final_args, single_url)
            cmdlines.append(final_args)

    # opera
    # * -private always implies a new window
    elif (arg0lc.endswith("opera.exe") or
            arg0lc.endswith("opera\\launcher.exe") or
            arg0lc.endswith("operaportable.exe") or
            arg0lc.endswith("opera-portable.exe")):
        final_args = args[:]  # copy

        if private_mode:
            final_args = _insertopt(final_args, "-private")
        elif new_window:
            final_args = _insertopt(final_args, "-new-window")

        if not url:
            final_args.append("%1")
        else:
            final_args = _inserturls(final_args, url)
        cmdlines.append(final_args)

    # unknown browser
    # * one command line per URL
    else:
        if not url:
            url = ["%1"]
        for single_url in url:
            final_args = args[:]  # copy
            final_args = _inserturls(final_args, single_url)
            cmdlines.append(final_args)

    if execute:
        result = False
        for cl in cmdlines:
            if _launch(cl):
                result = True
        return result

    return cmdlines[0]

def explore_file(file):
    """
    Open file explorer at a given location (*file*, which may also be a folder).

    The ``file_explorer`` global setting is used if possible, otherwise Windows
    Explorer is invoked.

    *file* may be empty or ``None`` in which case the file explorer is executed
    with no particular location specified.
    """

    def _user_explorer(explore_cmd, file):
        # parse the file_explorer command line
        try:
            explore_args = cmdline_split(explore_cmd)
            explore_exe = explore_args[0]
            if len(explore_args) > 1:
                explore_args = cmdline_quote(explore_args[1:])
            else:
                explore_args = ""
        except:
            print("Failed to parse the file_explorer setting", file=sys.stderr)
            traceback.print_exc()
            return False

        # prepare args placeholders
        placeholders = {
            'file_nq': file,
            'name_nq': os.path.basename(file),
            'parent_nq': os.path.dirname(file),
            'dir_or_parent_nq': file if os.path.isdir(file) else os.path.dirname(file)}
        for k in ('file', 'name', 'parent', 'dir_or_parent'):
            placeholders[k] = cmdline_quote(placeholders[k + '_nq'])
            placeholders[k + '_q'] = cmdline_quote(placeholders[k + '_nq'],
                                                   force_quote=True)

        has_placeholder = False

        for k, v in placeholders.items():
            ph = "{{" + k + "}}"
            if ph in explore_args:
                has_placeholder = True
                explore_args = explore_args.replace(ph, v)

        if file and not has_placeholder:
            if len(explore_args):
                explore_args += " "
            explore_args += cmdline_quote(file)

        try:
            keypirinha_api.shell_execute(
                explore_exe, explore_args, "", "", None, -1)
        except:
            print("Failed to execute custom file_explorer", file=sys.stderr)
            traceback.print_exc()
            return False

        return True

    if not file:
        file = "" # in case file is None, False or 0

    # try to use user's file explorer
    explore_cmd = kp.settings().get_stripped("file_explorer", "external",
                                             unquote=False)
    if explore_cmd and _user_explorer(explore_cmd, file):
        return

    # default behavior, use Windows Explorer
    windir = shell_known_folder_path(kpwt.FOLDERID.Windows.value)
    shex_flags = (kpwt.SEE_MASK_NOASYNC |
                  kpwt.SEE_MASK_FLAG_NO_UI |
                  kpwt.SEE_MASK_INVOKEIDLIST)
    if file:
        if os.path.isdir(file):
            shex_flags = kpwt.SEE_MASK_NOASYNC | kpwt.SEE_MASK_FLAG_NO_UI
            keypirinha_api.shell_execute(
                file, "", "",       # thing, args, working dir
                "", shex_flags, -1) # verb, flags, show
        else:
            keypirinha_api.shell_execute(
                os.path.join(windir, "explorer.exe"), # thing
                "/select," + cmdline_quote(file),     # args
                os.path.dirname(file),                # working dir
                "", shex_flags, -1)                   # verb, flags, show
    else:
        keypirinha_api.shell_execute(
            os.path.join(windir, "explorer.exe"),
            "", "", "", shex_flags, -1)

def execute_default_action(plugin, catalog_item, catalog_action):
    """
    Executes a default :py:class:`keypirinha.CatalogAction` using a given
    :py:class:`keypirinha.CatalogItem` object. *plugin* is the calling
    :py:class:`keypirinha.Plugin` object.
    """
    if not isinstance(catalog_item, keypirinha_api.CatalogItem):
        raise TypeError('catalog_item')
    if catalog_action is not None and not catalog_action.app_owned():
        return False

    if catalog_item.category() == kp.ItemCategory.FILE:
        final_target = catalog_item.target()
        final_args = catalog_item.raw_args()
        final_verb = None
        final_flags = None

        if catalog_action is None or catalog_action.name() == "open":
            final_verb = ""

        elif catalog_action.name() == "edit":
            editor_cmd = kp.settings().get_stripped("editor", "external",
                                                    unquote=False)
            if editor_cmd:
                try:
                    editor_args = cmdline_split(editor_cmd)
                    if not editor_args[0]:
                        editor_cmd = None # fall back to default behavior
                    else:
                        editor_args.append(catalog_item.target())
                        final_target = editor_args[0]
                        final_args = cmdline_quote(editor_args[1:])
                        final_verb = ""
                        final_flags = None
                except:
                    print("Failed to parse the 'editor' setting", file=sys.stderr)
                    traceback.print_exc()
                    editor_cmd = None # fall back to default behavior

            # default behavior
            # * use Shell's "edit" verb bindly
            # * NOTE: this verb is not associated with every type of files
            if not editor_cmd:
                final_target = catalog_item.target()
                final_args = ""
                final_verb = "edit"
                final_flags = None

        elif catalog_action.name() == "runas":
            final_verb = "runas"

        elif catalog_action.name() == "openwith":
            final_verb = "openas"
            final_flags = 0x100|0xC # SEE_MASK_NOASYNC|SEE_MASK_INVOKEIDLIST

        elif catalog_action.name() == "explore" or catalog_action.name() == "explore_resolved_path":
            file_to_show = catalog_item.target()
            if catalog_action.name() == "explore_resolved_path":
                try:
                    link_info = read_link(catalog_item.target())
                    if link_info and not link_info['is_msi']:
                        file_to_show = link_info['target']
                except IOError:
                    pass

            explore_file(file_to_show)
            return True

        elif catalog_action.name() == "properties":
            final_verb = "properties"
            final_flags = 0x400|0xC # SEE_MASK_FLAG_NO_UI|SEE_MASK_INVOKEIDLIST

        elif catalog_action.name() == "security":
            final_args = "Security"
            final_verb = "properties"
            final_flags = 0x100|0x400|0xC # SEE_MASK_NOASYNC|SEE_MASK_FLAG_NO_UI|SEE_MASK_INVOKEIDLIST

        elif catalog_action.name() == "copy_path":
            set_clipboard(catalog_item.target())
            return True

        elif catalog_action.name() == "copy_resolved_path":
            try:
                link_info = read_link(catalog_item.target())
            except IOError:
                link_info = None

            if link_info and not link_info['is_msi']:
                set_clipboard(link_info['target'])
            else:
                set_clipboard(catalog_item.target())

            return True

        elif catalog_action.name() == "print":
            final_verb = "print"

        else:
            # unknown action, just shell_execute the item with the default verb
            final_verb = ""

        if final_verb is not None:
            if os.path.isdir(final_target):
                explore_file(final_target)
            else:
                try:
                    shell_execute(
                        final_target, final_args,
                        verb=final_verb, api_flags=final_flags)
                except (FileNotFoundError, OSError) as exc:
                    print("Failed to execute {} (action {}). Error: {}".format(
                        catalog_item.target(),
                        str(catalog_action.label()) if catalog_action is not None else "None",
                        str(exc)),
                        file=sys.stderr)

            return True # action has been processed

    elif catalog_item.category() == kp.ItemCategory.URL:
        if catalog_action is not None and catalog_action.name() == "copy":
            set_clipboard(catalog_item.target())
            return True
        else:
            proto = urllib.parse.urlparse(catalog_item.target())[0].lower()
            if proto in ("http", "https", "ftp"):
                private_mode = None
                if catalog_action is not None and catalog_action.name() == "browse_private":
                    private_mode = True
                web_browser_command(
                    private_mode=private_mode,
                    url=catalog_item.target(),
                    execute=True)
                return True
            else:
                shell_execute(catalog_item.target())
                return True

    return False



#-------------------------------------------------------------------------------
# DEPRECATED STUFF
#-------------------------------------------------------------------------------

def slurp_text_file(file):
    """
    .. deprecated:: 2.5.3
        Use :py:func:`chardet_slurp` instead
    """
    return chardet_slurp(file)
