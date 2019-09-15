#
# Keypirinha: a fast launcher for Windows (keypirinha.com)
# Copyright 2013-2018 Jean-Charles Lefebvre <polyvertex@gmail.com>
#

import keypirinha_api
import enum
import os
import time
import inspect

# This module implements functions that can be used by third-party plugins.
# While some of them are just simple wrappers that directly call functions of
# the keypirinha_api built-in module, plugin developer should not be tempted to
# directly use the keypirinha_api features since its ABI may change often and
# break compatibility with previous versions.

def name():
    """Return application's name (e.g.: ``keypirinha``)."""
    return keypirinha_api.name()

def label():
    """Return application's display name (e.g.: ``Keypirinha``)."""
    return keypirinha_api.label()

def version():
    """
    Return application's version in a tuple of unsigned integers that can be
    used for comparison. Format is ``(major, minor, patch)``.

    Examples:
    ::
        version() > (2, )   # test if version is strictly greater than v2
        version() <= (1, 1) # test if version is less than or equal to v1.1
    """
    return keypirinha_api.version_tuple()

def version_string():
    """
    Return application's version in a dotted string as in ``M.mm.pppp`` where
    *M* is the major version number, *m* the minor number, and *p* is the patch
    revision. Prefer :py:func:`version` if the intent is to compare versions.
    """
    return keypirinha_api.version_string()

def arch():
    """Return current architecture model (i.e. ``x86`` or ``x64``)"""
    return keypirinha_api.arch()

def pid():
    """
    Return the **main** process ID of the application.

    Note:
        This function should be preferred over :py:func:`os.getpid` if you want
        to get the PID of Keypirinha.
        Keypirinha's architecture might change in the future and, for example,
        Python plugins may have a dedicated process, separated from
        application's main process.
        This function will always return the PID of the main process of the
        application.
    """
    return os.getpid()

def computer_name():
    """
    Return computer's NetBIOS name.

    This is the name used when looking for computer-specific configuration
    files.
    """
    return keypirinha_api.computer_name()

def user_name():
    """
    Return current user's name.

    This is the name used when looking for user-specific configuration files.
    """
    return keypirinha_api.user_name()

def exe_path():
    """
    Return the full path to Keypirinha's bootstrap executable (i.e. not the
    architecture-specific executable).
    """
    return keypirinha_api.exe_path()

def packages_list():
    """Return a list of the names of the packages that are currently loaded."""
    return keypirinha_api.packages_list()

def live_package_dir(package_full_name=None):
    """
    Get the directory of a *live* package, or the base directory for
    :ref:`pack-live` in case *package_full_name* is not specified.

    Prefer to use :py:meth:`Plugin.get_package_cache_path` when possible.

    The base directory should look similar to
    :file:`%APPDATA%/Keypirinha/Packages` in installed mode and
    :file:`X:/Keypirinha/portable/Profile/Packages` in portable mode.

    Note:
        The base directory is guaranteed to exist, but not the directory of the
        given package. Thus it is the responsibility of the caller to create it
        if needed.

    See Also:
        :py:func:`exe_path`, :py:func:`installed_package_dir`,
        :py:func:`user_config_dir`, :py:func:`package_cache_dir`,
        :py:meth:`Plugin.get_package_cache_path`
    """
    if package_full_name is None:
        return keypirinha_api.live_packages_dir()
    else:
        return os.path.join(keypirinha_api.live_packages_dir(),
                            package_full_name)

def installed_package_dir(package_full_name=None):
    """
    Get the path of an *installed* package (i.e.: ``*.keypirinha-package``), or
    the base directory for :ref:`pack-installed` if *package_full_name* is not
    specified.

    The base directory should look similar to
    :file:`%APPDATA%/Keypirinha/InstalledPackages` in installed mode and
    :file:`X:/Keypirinha/portable/Profile/InstalledPackages` in portable mode.

    Note:
        The base directory is guaranteed to exist, but not the package itself.
        Thus it is the responsibility of the caller to create it if needed.

    See Also:
        :py:func:`exe_path`, :py:func:`live_package_dir`,
        :py:func:`user_config_dir`, :py:func:`package_cache_dir`,
        :py:meth:`Plugin.get_package_cache_path`
    """
    if package_full_name is None:
        return keypirinha_api.installed_packages_dir()
    else:
        return os.path.join(keypirinha_api.installed_packages_dir(),
                            package_full_name)

def user_config_dir():
    """
    Get the path to the directory dedicated to user's configuration.

    The base directory should look similar to :file:`%APPDATA%/Keypirinha/User`
    in installed mode and :file:`X:/Keypirinha/portable/Profile/User` in
    portable mode.

    Note:
        The directory is guaranteed to exist.

    See Also:
        :py:func:`exe_path`, :py:func:`live_package_dir`,
        :py:func:`installed_package_dir`, :py:func:`package_cache_dir`,
        :py:meth:`Plugin.get_package_cache_path`
    """
    return keypirinha_api.user_config_dir()

def package_cache_dir(package_full_name=None):
    """
    Get the cache directory of a package, or its base directory if
    *package_full_name* is not specified.

    The base directory should look similar to
    :file:`%LOCALAPPDATA%/Keypirinha/Packages` in installed mode and
    :file:`X:/Keypirinha/portable/Local/Packages` in portable mode.

    Note:
        The base directory is guaranteed to exist, but not the directory of the
        given package.

    See Also:
        :py:func:`exe_path`, :py:func:`live_package_dir`,
        :py:func:`installed_package_dir`, :py:func:`user_config_dir`,
        :py:meth:`Plugin.get_package_cache_path`
    """
    if package_full_name is None:
        return keypirinha_api.packages_cache_dir()
    else:
        return os.path.join(keypirinha_api.packages_cache_dir(),
                            package_full_name)

def settings():
    """
    Return the :py:class:`Settings` object associated with the application.

    Note:
        * Settings might change at any time if the end-user decides to edit the
          configuration file. In thise case, the application will notify every
          loaded plugins by calling :py:meth:`Plugin.on_events` with the
          :py:const:`Events.APPCONFIG` flag.
        * The values returned by the :py:class:`Settings` object are always
          up-to-date so you do not have to get a new object in case of a
          :py:meth:`Plugin.on_events` notification.
        * If the end-user did not overwrite any default value (e.g.: empty
          configuration file), the dictionary will always be populated with the
          values in use (i.e.: the default ones).

    See Also:
        :py:meth:`Plugin.load_settings`
    """
    return Settings(keypirinha_api.app_settings())

def load_settings(package_full_name=None):
    """
    Return the :py:class:`Settings` object associated with a *package*.

    Args:
        package_full_name (str): The name of the Package to load/get the
            settings from.
            This argument is optional (but recommended) because the application
            has the ability to match a calling thread with its source Package.
            Nevertheless, this association mechanism might fail in some rare
            conditions, in which case the application falls back on using the
            passed package name.

    Warning:
        :py:meth:`Plugin.load_settings` must be called instead, whenever it is
        possible.

    See Also:
        :py:meth:`Plugin.load_settings`, :py:func:`settings`
    """
    settings_id = keypirinha_api.settings_load(package_full_name)
    if settings_id is None:
        raise ValueError(
            "settings not loaded from package: {}".format(package_full_name))
    return Settings(settings_id)

def load_icon(sources, force_reload=False, package_full_name=None):
    """
    Load an icon if it has not been loaded already and return a handle to it.

    Args:
        sources (list): Can be a string in case of a single source or a list of
            strings. This argument allows to specify one or several image files
            that are meant to represent the **same** icon, with different sizes.
            For example, you may want to specify a single ``.ico`` file that
            holds all the desired dimensions, or a list containing several
            ``.png`` files. See the Notes below for more info.

        force_reload (bool): Force the icon to be reloaded. Raising this flag
            may impact user experience quite significantly because of bad
            performances. It is recommended to ensure icon sources really have
            been modified since the last time it has been loaded.

        package_full_name (str): The name of the Package to which this icon will
            be attached. The lifetime of an icon handle is bound to the lifetime
            of its parent Package. If the Package gets unloaded or reloaded, its
            resources will be freed automatically and any handle pointing to
            those resources will become invalid.
            This argument is optional because the application has the ability to
            match a calling thread with its source Package. Nevertheless, in
            some rare conditions (e.g.: the calling thread is a Python thread),
            this association might fail.

    Returns:
        IconHandle: A handle to the icon. :py:meth:`IconHandle.free` must be
        called explicitly if you plan to reload, override this icon.

    Raises:
        ValueError: The specified *sources* could not be read or loaded.

    Warning:
        Use :py:meth:`Plugin.load_icon` instead when possible when call site is
        in :py:class:`Plugin`.

    Note:
        * The lifetime of a loaded icon resource is tied to the lifetime of the
          *package* that owns this resource.
        * The uniqueness of an icon is defined by its associated *package*
          **and** its *sources* list.
        * Two :py:class:`IconHandle` objects may point to the same icon
          resource. If :py:meth:`IconHandle.free` is called on one of them, the
          second object will point to a non-existing icon unless
          :py:meth:`Plugin.load_icon` or :py:func:`load_icon` is called with the
          exact same *sources* list, for the same *package*.
        * The following image formats are supported: ``ICO``, ``PNG`` and
          ``JPEG``.
        * Formats can be mixed in the list passed as *sources* argument.
        * The image dimensions required at runtime by the application depend on
          system settings and application settings. However, in order to have a
          good user experience, an icon should be available in the following
          sizes: ``16x16``, ``32x32``, ``48x48`` and ``256x256`` pixels.
          If a required size has not been provided, the application will get the
          next greater size and scale down the image to the required dimensions
          with the best available quality filter.
        * The paths passed via the *sources* argument can point to:

          * A resource file (i.e.: a file stored in Package's archive or
            directory). Example: ``res://PackageName/icon.png`` (``PackageName``
            is redundant but mandatory). See :py:meth:`Plugin.package_full_name`
            to get full package name of a plugin.
          * A cached file (i.e.: a file stored in Package's Cache directory).
            Example: ``cache://PackageName/icon-file.ico`` (``PackageName`` is
            redundant but mandatory)
          * A Shell Resource Location, which is formated that way:
            ``"@<PE-path>,[-]<stringID>"``, where ``<PE-path>`` is
            the path to an executable or a DLL (environment variables are
            expanded), ``stringID`` is the ID of the icon to load from the
            module (**if prefixed with** ``-``), or the zero-based index of the
            resource to load from the module (**no prefix**).
            Examples:
              * ``@shell32.dll,-12692``
              * ``@%SystemRoot%\\system32\\shell32.dll,-12690``
              * ``@C:\\Dir\\App.exe,0``

    See Also:
        :py:meth:`IconHandle.free` and :py:meth:`Plugin.load_icon`
    """
    if isinstance(sources, str):
        sources = [sources]
    icon_id = keypirinha_api.load_icon(sources, force_reload, package_full_name)
    if icon_id is None:
        raise ValueError("failed to create icon from the given sources")
    return IconHandle(icon_id)

def should_terminate(wait_seconds=None):
    """
    Return a boolean to indicate whether the current task (thread) should return
    as soon as possible, without completing its job.

    Delayed tasks (i.e. scheduled with :py:func:`delay`) **must** call this
    function **frequently**. Especially at I/O operations boundaries (storage
    accesses and network communications).

    The optional *wait_seconds* argument allows to wait for a given amout of
    seconds before returning (can be a float), unless the return value turns
    ``True`` before the end of the period.
    This is useful in case you don't want to handle an incoming message from the
    application (typically :py:meth:`Plugin.on_suggest`) too quickly/often in
    order to avoid any flooding due to user typing her search (hard-drive
    scratching, IPC queries, network requests, ...).

    Returns:
        bool: ``True`` indicates the current task should **immediately** return
        and discard its results.
        The reasons this function might return True are:

        * Application is terminating
        * The package and/or plugin that owns the current task is being (or has
          been) reloaded.
        * The plugin message has been obsoleted by a new and equivalent one.
          For example a :py:meth:`Plugin.on_suggest` call has been made right
          after the current one because the end-user is still typing.
        * The current task is taking too long
        * Any other reason due to an internal failure and that requires the
          application to free its resources

    Warning:
        If calling from a :py:class:`Plugin`, :py:meth:`Plugin.should_terminate`
        should always be preferred as it is faster.
    """
    if wait_seconds is not None:
        end = time.perf_counter() + wait_seconds
        while time.perf_counter() < end:
            if keypirinha_api.should_terminate():
                return True
            time.sleep(0.06) # 60ms
    return keypirinha_api.should_terminate()

def delay(seconds, func):
    """
    Schedules a call to *func* in *seconds* seconds (:py:class:`float`).

    **TO BE IMPLEMENTED**

    Raises:
        ValueError: *seconds* value is invalid or *func* is not a callable.

    Warning:
        *callable* must call :py:func:`should_terminate` as frequently as
        possible during loops, or at boundaries of lengthy operations (typically
        I/O operations like disk accesses and network communications).

    See Also:
        :py:func:`should_terminate`
    """
    raise NotImplementedError


@enum.unique
class ItemCategory(enum.IntEnum):
    """
    The :py:meth:`CatalogItem.category` property of :py:class:`CatalogItem`.

    Item's category ID reflects the content of :py:meth:`CatalogItem.target`
    (i.e. not :py:meth:`CatalogItem.raw_args` or
    :py:meth:`CatalogItem.displayed_args`) and it helps the plugin to know what
    a given item is about.

    Note that it's almost solely for the exclusive use of the plugin as
    Keypirinha interprets this value only if the ID is a standard one (i.e.
    ``ERROR``, ``FILE``, ...) and for displaying purpose. For example, a
    ``FILE`` item will automatically be given an icon from the OS by Keypirinha
    if it doesn't have one already and if it has to be displayed on the GUI.

    When creating items, it is recommended to use a *standard* category as much
    as possible and only if its meaning perfectly matches the content of
    :py:meth:`CatalogItem.target`. Otherwise, plugin developer may prefer to
    create their own set of category IDs, starting with
    ``ItemCategory.USER_BASE + 1``. Example::

        MY_CUSTOM_ITEMCAT = keypirinha.ItemCategory.USER_BASE + 1
        MY_SECOND_CUSTOM_ITEMCAT = keypirinha.ItemCategory.USER_BASE + 2

    .. important::
        Category IDs are internally registered on a **per-plugin** basis. There
        will be no collision if two plugins, may they have the same parent
        package or not, define a category having the value ``USER_BASE + 1``
        with a different meaning.
    """

    #: An "error" item that cannot be executed. It is destined to show a
    #: warning/error message in the results list where a specific result would
    #: normally be expected by the user. It will be accepted by the application
    #: only as a **suggestion**. It cannot be part of the Catalog. The best
    #: usage example for it can be found in the official ``Calc`` plugin, which
    #: sets an ``ERROR`` item as a suggestion to indicate user her mathematical
    #: expression could not be evaluated.
    #: ``ERROR`` **items should be created with**
    #: :py:meth:`Plugin.create_error_item`.
    ERROR = 1

    #: Item is a keyword that will be triggered by the application or a plugin
    #: (i.e.: an internal command)
    KEYWORD = 10

    #: Item is a path to a file/dir/executable/...
    FILE = 20

    #: Item is a command line to be executed, given as-is to the operating
    #: system
    CMDLINE = 30

    #: Item is a url (http/ftp/mailto/...)
    URL = 40

    #: Item is an expression that has to be evaluated (e.g.: math, programming
    #: language, ...)
    EXPRESSION = 50

    #: Item is a reference/id that can be used/interpreted only by the plugin
    #: that created the CatalogItem object
    REFERENCE = 60

    #: Base category id for third-party plugins.
    #: Allowed range is [USER_BASE, USER_MAX].
    USER_BASE = 1000

    #: Maximum category id for third-party plugins.
    #: Allowed range is [USER_BASE, USER_MAX].
    USER_MAX = 0xFFFFFFFE

@enum.unique
class ItemArgsHint(enum.IntEnum):
    """
    The :py:meth:`CatalogItem.args_hint` property of :py:class:`CatalogItem`.
    """
    FORBIDDEN = 0 #: The item object does not accept arguments
    ACCEPTED = 1  #: The item object optionally accepts arguments
    REQUIRED = 2  #: The item object requires arguments

@enum.unique
class ItemHitHint(enum.IntEnum):
    """
    The :py:meth:`CatalogItem.hit_hint` property of :py:class:`CatalogItem`.
    """
    #: The item object will be added to History, including its arguments, if any
    KEEPALL = 0

    #: The item object will not be added to History
    IGNORE = 1

    #: The **initial** item object selected by the user will be added to History
    #: (omitting its arguments, if any)
    NOARGS = 2

@enum.unique
class Events(enum.IntEnum):
    """The *flags* passed to :py:meth:`Plugin.on_events`."""
    #: Application configuration has changed. Either because of a manual
    #: modification by the user, or because a change to an environment variable
    #: has impacted at least one value (in which case this flag is combined with
    #: ``ENV``).
    APPCONFIG = 0x1

    #: Package configuration has changed. Either because of a manual
    #: modification by the user, or because a change to an environment variable
    #: has impacted at least one value (in which case this flag is combined with
    #: ``ENV``).
    PACKCONFIG = 0x2

    #: At least one environment variable has been added/removed/modified.
    #: Note that if this change impacts application and/or package
    #: configuration, this flag is combined with ``APPCONFIG`` and/or
    #: ``PACKCONFIG``.
    ENV = 0x100

    #: One or several logical volume have been inserted, removed, connected or
    #: disconnected. This event can be related to a storage device, a media or a
    #: network volume.
    STORAGEDEV = 0x200

    #: System's network settings have been modified (via the
    #: ``Internet Properties`` dialog for example), and plugins that perform
    #: network requests should update their state.
    #:
    #: Practically, it means :py:func:`keypirinha_net.build_urllib_opener`
    #: should be called in order to get a new opener object.
    #: This event usually goes along with the ``APPCONFIG`` event, but developer
    #: should not rely on this behavior.
    NETOPTIONS = 0x400

    #: The content of the Desktop has changed (common and/or user's).
    #: It can be because its structure has been modified (folders), or because
    #: some files/shortcuts have been added, modified, moved or removed.
    #:
    #: Keypirinha groups events from the file system a little before sending
    #: them to the plugins by waiting a couple of seconds in order to avoid
    #: flooding the plugins.
    #:
    #: **IMPORTANT:** Keypirinha will never send this notification if it is
    #: installed in one of the Desktop folders.
    DESKTOP = 0x1000

    #: The content of the Start Menu has changed (common and/or user's).
    #: It can be because its structure has been modified (folders), or because
    #: some files/shortcuts have been added, modified, moved or removed.
    #:
    #: Keypirinha groups events from the file system a little before sending
    #: them to the plugins by waiting a couple of seconds in order to avoid
    #: flooding the plugins.
    #:
    #: **IMPORTANT:** Keypirinha will never send this notification if it is
    #: installed in one of the Start Menu folders.
    STARTMENU = 0x2000

class Match(enum.IntEnum):
    """Match methods"""
    #: Match any item
    ANY = 0

    #: Match items against user's search terms using a fuzzy algorithm
    FUZZY = 1000

    #: Default behavior: ``FUZZY``
    DEFAULT = FUZZY

class Sort(enum.IntEnum):
    """Sort methods"""
    #: Do not sort items
    NONE = 0

    #: Sort results alphabetically by target (ascending)
    TARGET_ASC = 100

    #: Sort results alphabetically by label (ascending)
    LABEL_ASC = 200

    #: Sort results by descending score (for now, this sort method must be
    #: combined with :py:const:`Match.FUZZY`).
    SCORE_DESC = 1000

    #: Default behavior: ``SCORE_DESC``
    DEFAULT = SCORE_DESC


class Plugin(keypirinha_api.Plugin):
    """
    Base class for third-party plugins.

    Note:
        Methods prefixed with ``on_`` are the only ones called by the
        application.
    """

    #: Flag to enable/disable output of :py:meth:`dbg`.
    #:
    #: Warning:
    #:     Redistributed plugins must always have this flag disabled.
    _debug = False

    def __new__(cls):
        instance = super(Plugin, cls).__new__(cls)
        # Ensure super()'s __init__ gets called in case the derived class
        # overrides it without doing "The Right Thing" (c).
        super(Plugin, instance).__init__()
        return instance

    def __init__(self):
        """
        Plugin's default constructor. When implementing a new plugin, it is good
        practice to call it::

            def __init__(self):
                super().__init__()
        """
        pass # super()'s default __init__ has been called by __new__ already

    def friendly_name(self):
        """
        Return plugin's friendly (short) name. I.e. its class name.

        See Also:
            :py:meth:`full_name`, :py:meth:`package_full_name`
        """
        return self.__class__.__name__

    def should_terminate(self, wait_seconds=None):
        """
        Return a boolean to indicate whether the current task should return as
        soon as possible, without completing its job.

        Plugins should call this method **frequently**. Especially at I/O
        operations boundaries (storage accesses and network communications).

        See :py:func:`keypirinha.should_terminate` for more info about the
        *wait_seconds* parameter.

        Note:
            * When calling code is from a :py:class:`Plugin`, it is preferred to
              call this method instead of the
              :py:func:`keypirinha.should_terminate` function as it is
              potentially faster.
            * Check the documentation of :py:func:`keypirinha.should_terminate`
              to know more about the meaning of the returned value.

        See Also:
            :py:func:`keypirinha.should_terminate`
        """
        if super().should_terminate():
            return True
        return globals()['should_terminate'](wait_seconds)

    def info(self, *objects, sep=" "):
        """
        Log an informational message.

        *objects* and *sep* arguments are handled the same way than
        :py:func:`print`.

        See Also:
            :py:meth:`warn`, :py:meth:`err`, :py:meth:`dbg`
        """
        self.log(*objects, sep=sep, level=1)

    def warn(self, *objects, sep=" "):
        """
        Log a warning message.

        *objects* and *sep* arguments are handled the same way than
        :py:func:`print`.

        See Also:
            :py:meth:`info`, :py:meth:`err`, :py:meth:`dbg`
        """
        self.log(*objects, sep=sep, level=2)

    def err(self, *objects, sep=" "):
        """
        Log an error message.

        *objects* and *sep* arguments are handled the same way than
        :py:func:`print`.

        See Also:
            :py:meth:`info`, :py:meth:`warn`, :py:meth:`dbg`
        """
        self.log(*objects, sep=sep, level=3)

    def dbg(self, *objects, sep=" "):
        """
        Log a debug message.

        *objects* and *sep* arguments are handled the same way than
        :py:func:`print`.

        Note:
            By default, this method will produce no output unless the
            :py:attr:`keypirinha.Plugin._debug` flag is ``True``.

        Warning:
            Use this method only temporarily, in order to debug your plugin. May
            you wish to redistribute it. The :py:attr:`keypirinha.Plugin._debug`
            flag must be left untouched and no call to this method should be
            present in plugin's source code.

        See Also:
            :py:meth:`info`, :py:meth:`warn`, :py:meth:`err`
        """
        if self._debug:
            try:
                frameinfo = inspect.getframeinfo(inspect.stack()[1][0])
                lineno = int(frameinfo.lineno)
            except AttributeError:
                # This can happen (error: 'module' does not have an attribute
                # name 'getframeinfo'). Perhaps a GIL issue?
                lineno = -1
            if not objects:
                self.log("<TRACE>", sep=sep, level=1, lineno=lineno)
            else:
                self.log("DEBUG:", *objects, sep=sep, level=1, lineno=lineno)

    def log(self, *objects, sep=" ", level=1, lineno=-1):
        """
        Log a message.

        Warning:
            This method is not meant to be used directly, prefer to call the
            :py:meth:`info`, :py:meth:`warn`, :py:meth:`err` or :py:meth:`dbg`
            methods instead.
        """
        keypirinha_api.log(
            self.full_name(), lineno, level,
            sep.join([o if isinstance(o, str) else str(o) for o in objects]))

    def create_action(self, name, label, short_desc="", data_bag=""):
        """
        Create a :py:class:`CatalogAction` object.

        Args:
            name (str): The name of the action, normally lowercased, no space.
                Words can be separated by an underscore (``_``).
            label (str): The display name of the action. This is the value the
                user will see.
            short_desc (str): An optional one-line description of the item. It
                will be displayed right under the label on the GUI.
            data_bag (str): The *data bag* is a string container, exclusively
                for the use of this plugin. Entirely optional and never read by
                the application.

        Returns:
            CatalogAction: The newly created action, associated to this plugin.

        Raises:
            ValueError: Action could not be created due to one or more invalid
                passed argument.

        Warning:
            :py:class:`CatalogAction` objects must always be created using this
            method.

        See Also:
            :py:meth:`set_actions`, :py:meth:`clear_actions`
        """
        action = keypirinha_api.CatalogAction(self.id(), name, label,
                                              short_desc, data_bag)
        if not action.valid():
            raise ValueError('invalid CatalogAction name "{}"'.format(name))
        return action

    def set_actions(self, category, actions_list):
        """
        Associate a given list of :py:class:`CatalogAction` to an
        :py:class:`ItemCategory`.

        Args:
            category (ItemCategory): The category of item to associate the
                actions with. If needed, you can assign the same list of actions
                with several categories by calling this method several times.
            actions_list (list): A list of :py:class:`CatalogAction` objects
                that have been created with :py:meth:`create_action`.

        Returns:
            int: The actual number of actions taken into account. Actions are
            filtered out when they don't belong to this plugin for example, or
            if :py:meth:`CatalogAction.valid` returns ``False``.

        See Also:
            :py:meth:`create_action`, :py:meth:`clear_actions`
        """
        return super().set_actions(category, actions_list)

    def clear_actions(self, category=None):
        """
        Clear the list of actions associated to a given
        :py:class:`ItemCategory`, or clear *all* actions associated to this
        plugin if *category* is ``None``.

        See Also:
            :py:meth:`create_action`, :py:meth:`set_actions`
        """
        if category is None:
            super().clear_all_actions()
        else:
            super().clear_actions(category)

    def create_item(
            self, category, label, short_desc, target, args_hint, hit_hint,
            loop_on_suggest=False, icon_handle=None, data_bag=None):
        """
        Create and return a :py:class:`CatalogItem` object.

        :py:class:`CatalogItem` is the angular stone of |project|. It is the
        only data unit a plugin can use to be referenced in the central Catalog.

        Args:
            category (ItemCategory): The category of the **target** of this
                item. Indeed, the *target* might be a
                :py:const:`ItemCategory.KEYWORD` whereas its argument might
                represent a mathematical :py:const:`ItemCategory.EXPRESSION` for
                example. In that case, this argument should be ``KEYWORD`` to
                reflect the content of the *target* property.
                Prefer :py:meth:`create_error_item` to easily create an item of
                the :py:const:`ItemCategory.ERROR` category.
            label (str): The display name of the item. This is the value the
                user will see. It must not be empty.
            short_desc (str): An optional one-line description of the item. It
                will be displayed right under the label on the GUI.
            target (str): This is the main property of :py:class:`CatalogItem`,
                the plugin can put whatever it needs to differentiate this item
                among others. **This value cannot be null** unless *category* is
                :py:const:`ItemCategory.ERROR`.
            args_hint (ItemArgsHint): Indicates how the GUI should behave with
                this item when it comes to specifying its arguments. For
                example, if *target* is the path to an executabe file (in which
                case *category* should be :py:const:`ItemCategory.FILE`), user
                might expect to be able to add extra arguments before executing
                this item: :py:const:`ItemArgsHint.ACCEPTED` is the logical
                choice here.
            hit_hint (ItemHitHint): Indicates how the application should deal
                with this item once it has been executed by the user, regarding
                the History.
            loop_on_suggest (bool): Indicates the GUI should call
                :py:meth:`on_suggest` as long as this flag is raised. This
                argument should be left ``False`` unless you know what you are
                doing.
            icon_handle (IconHandle): An optional icon handle to associate with
                this item. |project| always tries to find the icon to an item
                that fits the best. For example, if item is a
                :py:const:`ItemCategory.FILE`, the system icon normally
                associated with it will be displayed to the user so
                *icon_handle* should be left ``None``. Otherwise, the
                application will try to fall back to plugin's default icon, if
                any. Eventually, if no icon could be associated to this item,
                the default application icon will displayed.
            data_bag (str): An arbitrary string for the exclusive use of the
                plugin. The *data bag* is a modifiable and persistent property
                that will never be interpreted by the application and that can
                be used to transport some data meant to be associated with this
                specific item.

        Returns:
            CatalogItem: The newly created item, associated to this plugin.

        Warning:
            :py:class:`CatalogItem` objects must always be created using this
            method.

        Note:
            * :samp:`str(item_object)` is equivalent to
              :samp:`item_object.label()`.
            * May you wish to compare two item objects, the ``__eq__``,
              ``__ne__``, ``__lt__``, ``__le__``, ``__gt__``, ``__ge__`` and
              ``__hash__`` operators are implemented. They are fast and cheap
              since they use the internal unique id of the item, which is
              computed at construction time or when its arguments are updated.

        See Also:
            :py:meth:`create_error_item`
        """
        if target is None:
            target = ""
        if icon_handle is None:
            icon_handle = 0;
        elif isinstance(icon_handle, IconHandle):
            icon_handle = icon_handle.id
        else:
            raise ValueError("invalid icon handle")
        if data_bag is None:
            data_bag = ""

        return keypirinha_api.CatalogItem(
            self, category, label, short_desc, target,
            args_hint, loop_on_suggest, hit_hint, icon_handle, data_bag)

    def create_error_item(
            self, label, short_desc, target="error", icon_handle=None,
            data_bag=None):
        """
        Create and return a :py:class:`CatalogItem` object of the
        :py:const:`ItemCategory.ERROR` category.

        Note:
            * An ``ERROR`` item will only be accepted by the application as a
              suggestion. It cannot be part of plugin's Catalog.
            * Only one ``ERROR`` item is allowed per batch of suggestions. If
              plugin sends a list of suggestion containing several ``ERROR``
              items, only the first one will be kept.
            * *short_desc* will be copied to *label* if *label* is empty to
              limit unexpected behavior (items with an empty label are filtered
              out by the application so the ``ERROR`` item would not be
              displayed).

        See Also:
            :py:meth:`create_item`
        """
        if len(label) == 0 and len(short_desc) > 0:
            label = short_desc
        return self.create_item(
            category=ItemCategory.ERROR,
            label=label,
            short_desc=short_desc,
            target=target,
            args_hint=ItemArgsHint.FORBIDDEN,
            hit_hint=ItemHitHint.IGNORE,
            loop_on_suggest=False,
            icon_handle=icon_handle,
            data_bag=data_bag)

    def set_suggestions(
            self, suggestions,
            match_method=Match.DEFAULT, sort_method=Sort.DEFAULT):
        """
        Offer some suggestions to the user according to the current search
        terms. This method is meant to be called from :py:meth:`on_suggest`.

        *suggestions* must be a list of :py:class:`CatalogItem` objects.

        *match_method* must be a :py:class:`Match` value.

        *sort_method* must be a :py:class:`Sort` value.

        Note:
            The *match_method* and *sort_method* arguments are taken into
            account by the application only if the user has selected an item
            already (i.e. not at first step of the search). That is, when the
            *items_chain* argument of :py:meth:`on_suggest` is not empty.
        """
        if isinstance(suggestions, tuple):
            suggestions = list(suggestions)
        elif not isinstance(suggestions, list):
            raise ValueError("suggestions arg must be a list or a tuple")

        if match_method not in Match:
            raise ValueError("invalid Match value")
        if sort_method not in Sort:
            raise ValueError("invalid Sort value")
        if sort_method == Sort.SCORE_DESC and match_method != Match.FUZZY:
            raise ValueError("invalid Match and Sort combination")

        super().set_suggestions(suggestions, match_method, sort_method)

    def has_resource(self, relative_path):
        """
        Check if plugin's parent package embeds a specific resource.

        Args:
            relative_path (str): The relative path to the desired resource file
                located in the package. Examples: ``resource.png``,
                ``subdir/resource.png``.
        """
        return super().has_resource(relative_path)

    def find_resources(self, name_pattern):
        """
        Return a list of resources in this package that match a given pattern.

        Args:
            name_pattern (str): The pattern to match the **name** part of the
                resource(s). Accepted wildcards are ``*`` (i.e.: matches zero or
                several characters), and ``?`` (matches a single character).

        Returns:
            list: The list of the relative paths to the matched resources. May
            be empty.
        """
        return super().find_resources(name_pattern)

    def load_binary_resource(self, relative_path):
        """
        Return a :py:class:`bytes` object holding the unmodified content of the
        specified resource.

        Raises:
            FileNotFoundError: The resource could not be found.
            IOError: Error while opening or reading the resource.
            RuntimeError: Unexpected/Unknown error.

        Note:
            For performance reason, the `MemoryError` exception is raised if the
            specified file size is bigger than 16MB (16777216 bytes).

        See Also:
            :py:meth:`load_text_resource`
        """
        return super().load_binary_resource(relative_path)

    def load_text_resource(self, relative_path):
        """
        Return a :py:class:`str` object holding the content of the specified
        resource.

        May raise the same exceptions than :py:meth:`load_binary_resource`, plus
        the :py:exc:`TypeError` exception if resource's content could not be
        decoded (Unicode error).

        See Also:
            :py:meth:`load_binary_resource`
        """
        return super().load_text_resource(relative_path)

    def get_package_cache_path(self, create=False):
        """
        Return the absolute path to package's cache directory.

        It is the responsibility of the caller to create it if it doesn't exist
        (either manually or by setting the 'create' argument to True). However,
        its parent directory is guaranteed to exist.
        The *create* flag allows to ask this method to create the directory for
        you.

        The cache directory (or *temp* directory) of a Package is common to
        every plugin of a **same** package and provides a physical storage area
        that can be used by plugins to store temporary data that may be manually
        deleted by the end-user between two runtime sessions.

        Raises:
            RuntimeError: Failed to get package's cache directory
            OSError: Failed to create the directory (in case *create* argument
                is ``True``).

        See Also:
            :py:meth:`package_cache_dir`
        """
        cache_dir = globals()['package_cache_dir'](self.package_full_name())
        if create and not os.path.exists(cache_dir):
            os.mkdir(cache_dir) # might raise an OSError exception
        return cache_dir

    def load_settings(self):
        """
        Return the :py:class:`keypirinha.Settings` object associated with the
        parent Package.

        Note:
            * The configuration file(s) will be loaded only the first time this
              method is called. Any subsequent call will return a new
              :py:class:`keypirinha.Settings` object pointing to the same data
              block.
            * When the application detects that one or several configuration
              files have been modified in a Package, it is automatically re-read
              the files (only if they were previously loaded), then will notify
              every related plugin via a call to :py:func:`Plugin.on_events`.
            * It is not necessary to re-call this method upon a
              :py:func:`Plugin.on_events` if you already have a
              :py:class:`keypirinha.Settings` object associated to this plugin.
              The application update user's configuration data upon file change.

        See Also:
            :py:func:`settings`
        """
        return globals()['load_settings'](self.package_full_name())

    def load_icon(self, sources, force_reload=False):
        """
        Load or get an :py:class:`IconHandle`.
        See :py:func:`load_icon` for more details.
        """
        return globals()['load_icon'](sources, force_reload,
                                      self.package_full_name())

    def set_default_icon(self, icon_handle):
        """
        Set the default icon of the catalog items created by this plugin.

        Args:
            icon_handle (IconHandle): the default icon handle to be used
        """
        if not isinstance(icon_handle, IconHandle):
            raise ValueError("IconHandle object expected")
        super().set_default_icon(icon_handle.id)


class IconHandle:
    """
    An opaque handle object created by :py:meth:`Plugin.load_icon` and
    by :py:func:`load_icon`.
    """
    def __init__(self, icon_id):
        self.id = icon_id

    def __bool__(self):
        """Indicate whether this handle has been :py:meth:`free` or not."""
        return self.id != 0

    def is_init(self):
        """
        .. deprecated:: 2.9.6
            Use standard :py:meth:`__bool__` operator instead
        """
        return self.id != 0

    def free(self):
        """
        Frees the icon associated with this handle.

        Returns:
            bool: A boolean value to indicate whether resources have actually
            been freed or not. This method may return ``False`` if it has been
            called already for this handle, or by an other
            :py:class:`IconHandle` object pointing to the same icon resource.
            You usually do not need to check the return value.

        Warning:
            This method must be called **explicitly**. It will **not** be called
            by the destructor of this object.
        """
        if self.id != 0:
            freed = keypirinha_api.free_icon(self.id)
            self.id = 0
            return freed
        return False


class Settings:
    """
    A class to access the Settings of a Package/Plugin.

    It is not meant to be instantiated manually: :py:meth:`Plugin.load_settings`
    should be called instead, or :py:func:`settings`.
    """

    def __init__(self, settings_id):
        self.settings_id = settings_id

    def sections(self):
        """Return a list of the loaded sections, or an empty list."""
        return keypirinha_api.settings_sections(self.settings_id)

    def keys(self, section=None):
        """Return a list of the keys found in *section*, or an empty list."""
        return keypirinha_api.settings_keys(self.settings_id, section)

    def has_section(self, section):
        """Check the existence of *section* and return a boolean."""
        return keypirinha_api.settings_has_section(self.settings_id, section)

    def has(self, key, section=None):
        """
        Check the existence of a *key* in a *section* and return a boolean.
        """
        return keypirinha_api.settings_has(self.settings_id, section, key)

    def get(self, key, section=None, fallback=None, unquote=False):
        """
        Get the string value of the specified *key* in *section*.

        Args:
            key (str): The name of the setting to find
            section (str): You can optionally specify a section name.
                Otherwise the key will be searched in the default section.
            fallback (any): A fallback value in case *key* does not exist in the
                specified *section*.
            unquote (bool): Unquote the resulting value if it is encapsulated by
                a pair of single-quotes ``'`` or by a pair of double-quotes
                ``"``.

        Returns:
            str: The found value, or *fallback* in case *key* was not found in
            *section*.
        """
        value = keypirinha_api.settings_get(self.settings_id, section, key)
        if value is None:
            return fallback
        if unquote:
            stripped_value = value.strip()
            if len(stripped_value) >= 2 and (
                    (stripped_value[0] == '"' and stripped_value[-1] == '"') or
                    (stripped_value[0] == "'" and stripped_value[-1] == "'")):
                value = stripped_value[1:-1]
        return value

    def get_stripped(self, key, section=None, fallback=None, unquote=True):
        """
        Same as :py:meth:`get` but :py:meth:`str.strip` the value and returns
        *fallback* if the value is **empty** or not found.

        Warning:
            The read value is unquoted **before** being stripped if the
            *unquote* argument is true, which means that if configuration value
            is ``" X "`` for example, ``X`` will be returned (i.e. no quotes, no
            spaces).
        """
        value = self.get(key, section, fallback="", unquote=unquote).strip()
        return fallback if len(value) == 0 else value

    def get_multiline(self, key, section=None, fallback=[],
                      keep_empty_lines=False):
        """
        A specialized :py:meth:`get` to read multiline values.
        It returns a list of lines (strings).

        A copy of the *fallback* argument is returned if the setting was not
        found or if the read value is empty (i.e. no line remains after the
        *keep_empty_lines* option has been applied).
        """
        value = keypirinha_api.settings_get(self.settings_id, section, key)
        if value is None:
            return fallback[:]
        lines = [ln.strip() for ln in iter(value.splitlines())
                    if keep_empty_lines or len(ln.strip()) > 0]
        return lines if len(lines) > 0 else fallback[:]

    def get_bool(self, key, section=None, fallback=None):
        """
        A specialized :py:meth:`get` to read boolean values.

        Values ``1``, ``y``, ``yes``, ``t``, ``true``, ``on``, ``enable`` and
        ``enabled`` are evaluated to ``True``.
        Values ``0``, ``n``, ``no``, ``f``, ``false``, ``off``, ``disable`` and
        ``disabled`` are evaluated to ``False``.
        The *fallback* argument is returned otherwise.

        Note:
            The read value, if any, is unquoted then stripped first.
        """
        value = self.get_stripped(key, section, fallback=None, unquote=True)
        if value is None:
            return fallback
        value = value.strip().lower()
        if len(value) == 0:
            return fallback
        if value in ('1', 'y', 'yes', 't', 'true', 'on', 'enable', 'enabled'):
            return True
        if value in ('0', 'n', 'no', 'f', 'false', 'off', 'disable',
                     'disabled'):
            return False
        return fallback

    def get_int(self, key, section=None, fallback=None, min=None, max=None):
        """
        A specialized :py:meth:`get` to read integer values.

        If the read value is successfully converted to an integer, it is
        **capped** against optional boundaries *min* and/or *max*.

        The *fallback* argument is returned in case the setting was not found or
        the format of the read value is incorrect.

        Note:
            * The ``int(value, base=0)`` expression is used to convert the read
              string value. So decimal representations are accepted as well as
              the hexadecimal (e.g. ``0xA3``), the octal (e.g. ``0o17``) and the
              binary (e.g. ``0b110``) ones.
            * The read value, if any, is unquoted then stripped first.
        """
        value = self.get_stripped(key, section, fallback=None, unquote=True)
        if value is None:
            return fallback
        try:
            if len(value) == 0:
                return fallback
            value = int(value, base=0)
            if min is not None and value < min:
                return min
            elif max is not None and value > max:
                return max
            else:
                return value
        except ValueError:
            return fallback

    def get_float(self, key, section=None, fallback=None, min=None, max=None):
        """
        A specialized :py:meth:`get` to read float values.

        If the read value is successfully casted/converted to a float, it is
        **capped** against *min* and *max* optional boundaries.

        The *fallback* argument is returned in case the setting was not found or
        the format of the read value is incorrect.

        Note:
            The read value, if any, is unquoted then stripped first.
        """
        value = self.get_stripped(key, section, fallback=None, unquote=True)
        if value is None:
            return fallback
        try:
            if len(value) == 0:
                return fallback
            value = float(value)
            if min is not None and value < min:
                return min
            elif max is not None and value > max:
                return max
            else:
                return value
        except ValueError:
            return fallback

    def get_enum(self, key, section=None, fallback=None, enum=[],
                 case_sensitive=False, unquote=True):
        """
        A specialized :py:meth:`get` to read enum values.

        The *enum* argument is the list of accepted string values.
        Comparison depends on the *case_sensitive* argument.

        The *fallback* argument is returned in case none of the enumerated
        values matches to the read value, or if the setting was not found.

        Note:
            The read value, if any, is unquoted (depending on the *unquote*
            argument) then stripped before being compared.
        """
        value = self.get_stripped(key, section, fallback=None, unquote=unquote)
        if value is None:
            return fallback
        value = value.strip()
        if value in enum:
            return value
        if not case_sensitive:
            value = value.lower()
            for e in enum:
                if value == e.lower():
                    return e
        return fallback

    def get_mapped(self, key, section=None, fallback=None, map={},
                   case_sensitive=False, unquote=True):
        """
        A specialized :py:meth:`get` to read mapped values.

        The *map* argument is a dictionary where keys are strings that are
        expected to be read from the configuration data (similar behavior to
        :py:meth:`get_enum`), and their respective values are the ones that are
        returned by this method in case one of the keys has been matched.

        Comparison of the read value and the keys depend on the *case_sensitive*
        argument.

        The *fallback* argument is returned in case none of the keys matches to
        the read value, or if the setting was not found.

        Note:
            The read value, if any, is unquoted (depending on the *unquote*
            argument) then stripped before being compared.
        """
        value = self.get_stripped(key, section, fallback=None, unquote=unquote)
        if value is None:
            return fallback
        value = value.strip()
        if value in map:
            return map[value]
        if not case_sensitive:
            value = value.lower()
            for k in map.keys():
                if value == k.lower():
                    return map[k]
        return fallback



#-------------------------------------------------------------------------------
# DEPRECATED STUFF
#-------------------------------------------------------------------------------

def packages_path():
    """
    .. deprecated:: 2.1
        Use :py:func:`live_package_dir` instead
    """
    return live_package_dir()

def package_path(full_name):
    """
    .. deprecated:: 2.1
        Use :py:func:`live_package_dir` instead
    """
    return live_package_dir(full_name)
