#
# Keypirinha: a fast launcher for Windows (keypirinha.com)
# Copyright 2013-2018 Jean-Charles Lefebvre <polyvertex@gmail.com>
#

import ctypes as ct
from ctypes.wintypes import *
import enum
import os.path
import string
import uuid


kernel32 = ct.windll.kernel32
user32 = ct.windll.user32
shell32 = ct.windll.shell32
ole32 = ct.windll.ole32

# in addition to ctypes.wintypes
LRESULT = LPARAM
LONG_PTR = LPARAM
ULONG_PTR = WPARAM
PVOID = ct.c_void_p
PWSTR = ct.c_wchar_p
WNDPROCTYPE = ct.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)


DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6

@enum.unique
class FOLDERID(enum.Enum):
    """
    An enum of GUID strings of ``KNOWNFOLDERID``, referenced by name

    .. note::
        Exhaustive list of ``KNOWNFOLDERID`` references:
        ``https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx``
    """
    AccountPictures = "{008ca0b1-55b4-4c56-b8a8-4de4b299d3be}" #: ``%APPDATA%\Microsoft\Windows\AccountPictures``
    CameraRoll = "{ab5fb87b-7ce2-4f83-915d-550846c9537b}" #: ``%USERPROFILE%\Pictures\Camera Roll`` (Win8.1+)
    CommonStartMenu = "{a4115719-d62e-491d-aa7c-e74b8be3b067}" #: ``%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu``
    CommonStartup = "{82a5ea35-d9cd-47c5-9629-e15d2f714e6e}" #: ``%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs\StartUp``
    Contacts = "{56784854-c6cb-462b-8169-88e350acb882}" #: ``%USERPROFILE%\Contacts``
    Desktop = "{b4bfcc3a-db2c-424c-b029-7fe99a87c641}" #: ``%USERPROFILE%\Desktop``
    Documents = "{fdd39ad0-238f-46af-adb4-6c85480369c7}" #: ``%USERPROFILE%\Documents``
    Downloads = "{374de290-123f-4565-9164-39c4925e467b}" #: ``%USERPROFILE%\Downloads``
    Favorites = "{1777f761-68ad-4d8a-87bd-30b759fa33dd}" #: ``%USERPROFILE%\Favorites``
    Fonts = "{fd228cb7-ae11-4ae3-864c-16f3910ab8fe}" #: ``%windir%\Fonts``
    Links = "{bfb9d5e0-c6a9-404c-b2b2-ae6db6af4968}" #: ``%USERPROFILE%\Links``
    LocalAppData = "{f1b32785-6fba-4fcf-9d55-7b8e7f157091}" #: ``%LOCALAPPDATA%`` (``%USERPROFILE%\AppData\Local``)
    LocalAppDataLow = "{a520a1a4-1780-4ff6-bd18-167343c5af16}" #: ``%USERPROFILE%\AppData\LocalLow``
    Music = "{4bd8d571-6d19-48d3-be97-422220080e43}" #: ``%USERPROFILE%\Music``
    Pictures = "{33e28130-4e1e-4676-835a-98395c3bc3bb}" #: ``%USERPROFILE%\Pictures``
    Playlists = "{de92c1c7-837f-4f69-a3bb-86e631204a23}" #: ``%USERPROFILE%\Music\Playlists``
    Profile = "{5e6c858f-0e22-4760-9afe-ea3317b67173}" #: ``%USERPROFILE%`` (``%SystemDrive%\Users\%USERNAME%``)
    ProgramFiles = "{905e63b6-c1bf-494e-b29c-65b732d3d21a}" #: ``%ProgramFiles%``
    ProgramFilesX64 = "{6d809377-6af0-444b-8957-a3773f02200e}" #: ``%ProgramFiles%``
    ProgramFilesX86 = "{7c5a40ef-a0fb-4bfc-874a-c0f2e0b9fa8e}" #: ``%ProgramFiles(x86)%``
    ProgramFilesCommon = "{f7f1ed05-9f6d-47a2-aaae-29d317c6f066}" #: ``%ProgramFiles%\Common Files``
    ProgramFilesCommonX64 = "{6365d5a7-0f0d-45e5-87f6-0da56b6a4f7d}" #: ``%ProgramFiles%\Common Files``
    ProgramFilesCommonX86 = "{de974d24-d9c6-4d3e-bf91-f4455120b917}" #: ``%ProgramFiles(x86)%\Common Files``
    Programs = "{a77f5d77-2e2b-44c3-a6a2-aba601054a51}" #: ``%APPDATA%\Microsoft\Windows\Start Menu\Programs``
    Public = "{dfdf76a2-c82a-4d63-906a-5644ac457385}" #: ``%PUBLIC%`` (``%SystemDrive%\Users\Public``)
    PublicDesktop = "{c4aa340d-f20f-4863-afef-f87ef2e6ba25}" #: ``%PUBLIC%\Desktop``
    PublicDocuments = "{ed4824af-dce4-45a8-81e2-fc7965083634}" #: ``%PUBLIC%\Documents``
    PublicDownloads = "{3d644c9b-1fb8-4f30-9b45-f670235f79c0}" #: ``%PUBLIC%\Downloads``
    PublicMusic = "{3214fab5-9757-4298-bb61-92a9deaa44ff}" #: ``%PUBLIC%\Music``
    PublicPictures = "{b6ebfb86-6907-413c-9af7-4fc2abf07cc5}" #: ``%PUBLIC%\Pictures``
    PublicVideos = "{2400183a-6185-49fb-a2d8-4a392a602ba3}" #: ``%PUBLIC%\Videos``
    RoamingAppData = "{3eb685db-65f9-4cf6-a03a-e3ef65729f3d}" #: ``%APPDATA%`` (``%USERPROFILE%\AppData\Roaming``)
    Screenshots = "{b7bede81-df94-4682-a7d8-57a52620b86f}" #: ``%USERPROFILE%\Pictures\Screenshots``
    SendTo = "{8983036c-27c0-404b-8f08-102d10dcfd74}" #: ``%APPDATA%\Microsoft\Windows\SendTo``
    SkyDrive = "{a52bba46-e9e1-435f-b3d9-28daa648c0f6}" #: ``%USERPROFILE%\OneDrive`` (Win8.1+)
    SkyDriveCameraRoll = "{767e6811-49cb-4273-87c2-20f355e1085b}" #: ``%USERPROFILE%\OneDrive\Pictures\Camera Roll`` (Win8.1+)
    SkyDriveDocuments = "{24d89e24-2f19-4534-9dde-6a6671fbb8fe}" #: ``%USERPROFILE%\OneDrive\Documents`` (Win8.1+)
    SkyDrivePictures = "{339719b5-8c47-4894-94c2-d8f77add44a6}" #: ``%USERPROFILE%\OneDrive\Pictures`` (Win8.1+)
    StartMenu = "{625b53c3-ab48-4ec1-ba1f-a1ef4146fc19}" #: ``%APPDATA%\Microsoft\Windows\Start Menu``
    Startup = "{b97d20bb-f46a-4c97-ba10-5e3608430854}" #: ``%APPDATA%\Microsoft\Windows\Start Menu\Programs\StartUp``
    System = "{1ac14e77-02e7-4e5d-b744-2eb1ae5198b7}" #: ``%windir%\system32``
    SystemX86 = "{d65231b0-b2f1-4857-a4ce-a8e7c6ea7d27}" #: ``%windir%\system32``
    UserProfiles = "{0762d272-c50a-4bb0-a382-697dcd729b80}" #: ``%SystemDrive%\Users``
    UserProgramFiles = "{5cd7aee2-2219-4a67-b85d-6c9ce15660cb}" #: ``%LOCALAPPDATA%\Programs``
    UserProgramFilesCommon = "{bcbd3057-ca5c-4622-b42d-bc56db0ae516}" #: ``%LOCALAPPDATA%\Programs\Common`` (Win7+)
    Videos = "{18989b1d-99b5-455b-841c-ab7c74e4ddfc}" #: ``%USERPROFILE%\Videos``
    Windows = "{f38bf404-1d43-42f2-9305-67de0b28fc23}" #: ``%windir%``

GWL_STYLE = -16
GWL_EXSTYLE = -20

GWLP_WNDPROC = -4
GWLP_HINSTANCE = -6
GWLP_HWNDPARENT = -8
GWLP_ID = -12
GWLP_USERDATA = -21

INFINITE = 0xFFFFFFFF

KF_FLAG_DEFAULT = 0x00000000
KF_FLAG_NOT_PARENT_RELATIVE = 0x00000200
KF_FLAG_DEFAULT_PATH = 0x00000400
KF_FLAG_INIT = 0x00000800
KF_FLAG_DONT_VERIFY = 0x00004000
KF_FLAG_CREATE = 0x00008000

SEE_MASK_DEFAULT = 0x0
SEE_MASK_CLASSNAME = 0x1
SEE_MASK_CLASSKEY = 0x3
SEE_MASK_IDLIST = 0x4
SEE_MASK_INVOKEIDLIST = 0xC
SEE_MASK_ICON = 0x10
SEE_MASK_HOTKEY = 0x20
SEE_MASK_NOCLOSEPROCESS = 0x40
SEE_MASK_CONNECTNETDRV = 0x80
SEE_MASK_NOASYNC = 0x100
SEE_MASK_DOENVSUBST = 0x200
SEE_MASK_FLAG_NO_UI = 0x400
SEE_MASK_UNICODE = 0x4000
SEE_MASK_NO_CONSOLE = 0x8000
SEE_MASK_ASYNCOK = 0x100000
SEE_MASK_NOQUERYCLASSSTORE = 0x1000000
SEE_MASK_HMONITOR = 0x200000
SEE_MASK_NOZONECHECKS = 0x800000
SEE_MASK_WAITFORINPUTIDLE = 0x2000000
SEE_MASK_FLAG_LOG_USAGE = 0x4000000
SEE_MASK_FLAG_HINST_IS_SITE = 0x8000000

SEM_FAILCRITICALERRORS = 0x1
SEM_NOGPFAULTERRORBOX = 0x2
SEM_NOOPENFILEERRORBOX = 0x8000

SW_HIDE = 0
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOW = 5
SW_SHOWDEFAULT = 10
SW_SHOWMAXIMIZED = 3
SW_SHOWMINIMIZED = 2
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_SHOWNOACTIVATE = 4
SW_SHOWNORMAL = 1

WAIT_ABANDONED = 0x80
WAIT_OBJECT_0 = 0x0
WAIT_TIMEOUT = 0x102
WAIT_FAILED = 0xFFFFFFFF

WM_QUIT = 0x12
WM_COPYDATA = 0x4A
WM_COMMAND = 0x0111
WM_USER = 0x0400


class COPYDATASTRUCT(ct.Structure):
    _fields_ = [("dwData", ULONG_PTR),
                ("cbData", DWORD),
                ("lpData", PVOID)]

class GUID(ct.Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)]

    def __init__(self, guid):
        super().__init__()
        uuid_ = guid if isinstance(guid, uuid.UUID) else uuid.UUID(guid)
        (self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1],
            tail) = uuid_.fields
        for idx in range(2, 8):
            self.Data4[idx] = tail >> (8 - idx - 1) * 8 & 0xff

#class SHELLEXECUTEINFO(ct.Structure):
#    _fields_ = [
#        ("cbSize", DWORD),
#        ("fMask", ULONG),
#        ("hwnd", HWND),
#        ("lpVerb", LPCWSTR),
#        ("lpFile", LPCWSTR),
#        ("lpParameters", LPCWSTR),
#        ("lpDirectory", LPCWSTR),
#        ("nShow", ct.c_int),
#        ("hInstApp", HINSTANCE),
#        ("lpIDList", LPVOID),
#        ("lpClass", LPCWSTR),
#        ("hkeyClass", HKEY),
#        ("dwHotKey", DWORD),
#        ("hUnion", HANDLE),
#        ("hProcess", HANDLE)]
#
#    def __init__(self):
#        super().__init__()
#        ct.memset(ct.addressof(self), 0, ct.sizeof(self))
#        self.cbSize = ct.sizeof(self)

class WNDCLASSEXW(ct.Structure):
    _fields_ = [("cbSize", UINT),
                ("style", UINT),
                ("lpfnWndProc", WNDPROCTYPE),
                ("cbClsExtra", ct.c_int),
                ("cbWndExtra", ct.c_int),
                ("hInstance", HINSTANCE),
                ("hIcon", HICON),
                ("hCursor", HANDLE),
                ("hBrush", HBRUSH),
                ("lpszMenuName", LPCWSTR),
                ("lpszClassName", LPCWSTR),
                ("hIconSm", HICON)]

class ScopedSysErrorMode:
    """
    A context manager to safely wraps a call to ``kernel32.SetThreadErrorMode``,
    then undo it on exit.
    """
    def __init__(self, desired_mode=SEM_NOOPENFILEERRORBOX|SEM_FAILCRITICALERRORS):
        self._desired_mode = desired_mode
        self._error = None
        self._old_mode = None

    def __enter__(self):
        try:
            old_mode = DWORD(0)
            if kernel32.SetThreadErrorMode(self._desired_mode, ct.byref(old_mode)):
                assert kernel32.GetThreadErrorMode() == self._desired_mode
                self._error = 0
                self._old_mode = old_mode.value
            else:
                self._error = kernel32.GetLastError()
                self._old_mode = None
        except AttributeError:
            self._error = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._error == 0 and self._old_mode is not None:
            kernel32.SetThreadErrorMode(self._old_mode, None)
            assert kernel32.GetThreadErrorMode() == self._old_mode
        self._error = None
        self._old_mode = None


def ZeroMemory(ctypes_obj):
    """A wrapper around Windows' ``ZeroMemory`` function"""
    ct.memset(ct.addressof(ctypes_obj), 0, ct.sizeof(ctypes_obj))

def declare_func(ctypes_dll, func_name, ret=None, args=[]):
    """
    Declare a DLL function by setting its ``ctypes`` attributes, and return
    function's callable.
    """
    func = getattr(ctypes_dll, func_name)
    func.restype = ret
    func.argtypes = args
    return func

def _import_func(ctypes_dll, func_name, *args, **kwargs):
    func = declare_func(ctypes_dll, func_name, *args, **kwargs)
    globals()[func_name] = func


MAKEINTRESOURCE = lambda n: ct.cast(n, ct.c_char_p)

_import_func(kernel32, "CloseHandle", ret=BOOL, args=[HANDLE])
_import_func(kernel32, "GetDiskFreeSpaceExW", ret=BOOL, args=[LPCWSTR, PULARGE_INTEGER, PULARGE_INTEGER, PULARGE_INTEGER])
_import_func(kernel32, "GetDriveTypeW", ret=UINT, args=[LPCWSTR])
_import_func(kernel32, "GetExitCodeProcess", ret=BOOL, args=[HANDLE, LPDWORD])
_import_func(kernel32, "GetFileAttributesW", ret=DWORD, args=[LPCWSTR])
_import_func(kernel32, "GetLastError", ret=DWORD)
_import_func(kernel32, "GetLogicalDrives", ret=DWORD)
_import_func(kernel32, "GetModuleHandleW", ret=HMODULE, args=[LPCWSTR])
_import_func(kernel32, "GetThreadErrorMode", ret=DWORD)
_import_func(kernel32, "SetLastError", args=[DWORD])
_import_func(kernel32, "SetThreadErrorMode", ret=BOOL, args=[DWORD, LPDWORD])
_import_func(kernel32, "TerminateProcess", ret=BOOL, args=[HANDLE, UINT])
_import_func(kernel32, "WaitForSingleObject", ret=DWORD, args=[HANDLE, DWORD])

_import_func(ole32, "CoTaskMemFree", args=[LPVOID])

_import_func(user32, "ChangeWindowMessageFilterEx", ret=BOOL, args=[HWND, UINT, DWORD, ct.c_void_p])
_import_func(user32, "CreateWindowExW", ret=HWND, args=[DWORD, LPCWSTR, LPCWSTR, DWORD, ct.c_int, ct.c_int, ct.c_int, ct.c_int, HWND, HANDLE, HINSTANCE, LPVOID])
_import_func(user32, "DefWindowProcW", ret=LRESULT, args=[HWND, UINT, WPARAM, LPARAM])
_import_func(user32, "DestroyWindow", ret=BOOL, args=[HWND])
_import_func(user32, "DispatchMessageW", ret=LRESULT, args=[LPMSG])
_import_func(user32, "FindWindowW", ret=HWND, args=[LPCWSTR, LPCWSTR])
_import_func(user32, "GetClassInfoExW", ret=BOOL, args=[HANDLE, LPCWSTR, ct.POINTER(WNDCLASSEXW)])
_import_func(user32, "MsgWaitForMultipleObjects", ret=DWORD, args=[DWORD, ct.POINTER(HANDLE), BOOL, DWORD, DWORD])
_import_func(user32, "PeekMessageW", ret=BOOL, args=[LPMSG, HWND, UINT, UINT, UINT])
_import_func(user32, "RegisterClassExW", ret=ATOM, args=[ct.POINTER(WNDCLASSEXW)])
_import_func(user32, "SendMessageW", ret=LRESULT, args=[HWND, UINT, WPARAM, LPARAM])
_import_func(user32, "TranslateMessage", ret=BOOL, args=[LPMSG])

_import_func(shell32, "SHGetKnownFolderPath", ret=ct.HRESULT, args=[ct.POINTER(GUID), DWORD, HANDLE, ct.POINTER(PWSTR)])
#_import_func(shell32, "ShellExecuteExW", ret=BOOL, args=[ct.POINTER(SHELLEXECUTEINFO)])

# 32/64 bit
try:
    GetWindowLongPtr = declare_func(user32, "GetWindowLongPtrW", ret=LONG_PTR, args=[HWND, ct.c_int])
    SetWindowLongPtr = declare_func(user32, "SetWindowLongPtrW", ret=LONG_PTR, args=[HWND, ct.c_int, LONG_PTR])
except AttributeError:
    GetWindowLongPtr = declare_func(user32, "GetWindowLongW", ret=LONG, args=[HWND, ct.c_int])
    SetWindowLongPtr = declare_func(user32, "SetWindowLongW", ret=LONG, args=[HWND, ct.c_int, LONG])


def get_logical_drives():
    """Get a list of the letters of the currently available disk drives."""
    drives = []
    bitmask = kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1
    return drives

def get_known_folder_path(folderid, flags=KF_FLAG_DONT_VERIFY, token=None):
    """
    A wrapper around ``shell32.SHGetKnownFolderPath`` that accepts a
    :py:class:`FOLDERID` reference, a `GUID` object, an :py:class:`uuid.UUID`
    object or a GUID string; and returns the path to the specified Known Folder.

    May raise a `TypeError`, `OSError` or `FileNotFoundError` exception
    """
    if isinstance(folderid, GUID):
        guid = folderid
    elif isinstance(folderid, FOLDERID):
        guid = GUID(folderid.value)
    elif isinstance(folderid, uuid.UUID):
        guid = GUID(folderid)
    elif isinstance(folderid, str):
        lokeys = {k.lower(): k for k in FOLDERID.__members__.keys()}
        if folderid.lower() in lokeys:
            # folderid is the FOLDERID name e.g. "Downloads"
            guid = GUID(FOLDERID[lokeys[folderid.lower()]].value)
        else:
            guid = GUID(folderid)
    else:
        raise TypeError("folderid")

    if flags & KF_FLAG_DONT_VERIFY:
        must_verify = False
    else:
        flags |= KF_FLAG_DONT_VERIFY
        must_verify = True

    path_ptr = ct.c_wchar_p()
    res = shell32.SHGetKnownFolderPath(ct.byref(guid), flags, token,
                                       ct.byref(path_ptr))
    if res:
        raise OSError("SHGetKnownFolderPath failed (code {})".format(res))
    result = path_ptr.value
    ole32.CoTaskMemFree(path_ptr)

    if must_verify and not os.path.exists(result):
        raise FileNotFoundError

    return result
