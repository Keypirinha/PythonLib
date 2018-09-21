# Keypirinha: a fast launcher for Windows (keypirinha.com)

import keypirinha as kp
import socket
import urllib.parse
import urllib.request
import ssl
import socks
import sockshandler

class UrllibOpener:
    """
    A replacement to :py:class:`urllib.request.OpenerDirector` to apply user's
    global settings if needed and to ensure reasonable default ``timeout`` value
    (i.e. too long hanging due to bad connection).

    This class is not meant to be used directly, see
    :py:func:`build_urllib_opener`.
    """
    def __init__(self, opener):
        if not isinstance(opener, urllib.request.OpenerDirector):
            raise TypeError
        self._opener = opener
        self._kp_timeout = kp.settings().get_int(
                    "timeout", section="network", fallback=5, min=1, max=60)

    def open(self, fullurl, *args, data=None, timeout=None, **kwargs):
        """
        This overrides :py:meth:`urllib.request.OpenerDirector.open` in order to
        apply the ``timeout`` value automatically from Keypirinha's settings.
        Forcing a *timeout* value here is still allowed but discouraged.
        """
        if timeout is None:
            timeout = self._kp_timeout
        if timeout is None:
            # this "Should Never Happen" (c) since Keypirinha already replaces
            # an empty value by the hard-coded default
            timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        return self._opener.open(
                        fullurl, *args, data=data, timeout=timeout, **kwargs)

    def __getattr__(self, name):
        return getattr(self._opener, name)

    def __setattr__(self, name, value):
        if name == "_opener":
            super().__setattr__(name, value)
        else:
            setattr(self._opener, name, value)

def build_urllib_opener(
        proxies=None, ssl_check_hostname=None,
        extra_handlers=[], extra_pre_handlers=[]):
    """
    A replacement to :py:func:`urllib.request.build_opener` that takes care of
    using current user's global settings (Keypirinha and/or system's) regarding
    network connections, by inserting and configuring one or several connection
    handlers (derived from :py:class:`urllib.request.BaseHandler`).

    Examples::

        # example 1
        opener = build_urllib_opener()
        with opener.open("http://httpbin.org/user-agent") as response:
            print(response.read())

        # example 2: HTTP proxy
        proxies = {'http': "http://proxy_user:proxy_pass@127.0.0.1:8080"}
        opener = build_urllib_opener(proxies)
        with opener.open("http://httpbin.org/ip") as response:
            print(response.read())

    Args:
        proxies (dict): A dictionary of proxies to pass to the constructor of
            :py:class:`urllib.request.ProxyHandler`, if any. Notes:

            * ``None`` (default; **recommended**) means proxies configured by
              the user at Keypirinha's level, or by default at system level will
              be used.
            * An empty dictionary (i.e. ``{}``) means **no** proxy will be
              configured regardless of user or machine settings. Note that going
              against user's will is against Keypirinha's design policy!
            * See the notes below about ``SOCKS`` proxies.
            * See :py:func:`proxies_list_to_dict` if you need to convert a list
              of proxies URLs into a dictionary.

        extra_handlers (list): A list/tuple of extra handlers to **append** to
            the final handlers chain before passing it to
            :py:func:`urllib.request.build_opener`.

        extra_pre_handlers (list): A list/tuple of extra handlers to **prepend**
            to the final handlers chain before passing it to
            :py:func:`urllib.request.build_opener`.

            **CAUTION:** This parameter is here for convenience and you should
            use it only if you know what you are doing as it may interfere with
            the handlers added by this function.

        ssl_check_hostname (bool): Should the hostname be checked against
            received security certificate? This argument is equivalent to
            tweaking with :py:attr:`ssl.SSLContext.check_hostname` and
            :py:attr:`ssl.SSLContext.verify_mode`.

            Default behavior of the ``urllib`` module (i.e. ``None`` value) is
            to check the hostname unless explicitely specified here (boolean),
            in which case this function will either add an
            :py:class:`urllib.request.HTTPSHandler` handler with the appropriate
            arguments to the chain, or, if caller already added a
            :py:class:`urllib.request.HTTPSHandler` handler (either in the
            *extra_handlers* or *extra_pre_handlers* list), it will be modified
            accordingly.

    Returns:
        UrllibOpener: A
        :py:class:`urllib.request.OpenerDirector`-compatible opener object.

    Note:
        Notes about ``SOCKS`` proxy support:

        * Support for ``SOCKS`` proxy (v4 and v5) is **experimental** and uses
          the `PySocks <https://github.com/Anorov/PySocks>`_ third-party module
          under the hood.
        * DNS requests do not go through the proxy server.
        * IPv6 connections through the proxy server are not supported.
        * Tests have shown that if proxies for several schemes have been
          specified, ``UNKNOWN_PROTOCOL`` SSL error may occurs under some
          circumstances. For that reason, if a ``SOCKS`` proxy is specified, it
          takes precedence over the other proxy servers that might be in the
          dictionary as well so they will be purely ignored by this function in
          favor of the ``SOCKS`` proxy.
    """
    def _has_handler(handler_type):
        for h in (*extra_pre_handlers, *extra_handlers):
            if isinstance(h, handler_type):
                return h
        return None

    own_handlers = []

    # get proxies from the application if needed
    if proxies is None:
        proxies = proxies_to_dict(kp.settings().get_multiline(
            "proxy", section="network", fallback=[], keep_empty_lines=False))

    # proxy servers
    if proxies is not None:
        # socks proxy
        # in case user specified a "socks" proxy, we have to extract it from the
        # dict and insert it as a different handler in the final handlers chain
        # since it is not supported by the standard urrlib module
        got_socks_proxy = False
        for scheme, proxy_url in proxies.items():
            scheme_lc = scheme.lower()
            if scheme_lc not in ("socks", "socks4", "socks5"):
                continue

            if scheme_lc == "socks4":
                proxy_type = socks.PROXY_TYPE_SOCKS4
            else:
                proxy_type = socks.PROXY_TYPE_SOCKS5

            proxy_info = urllib.parse.urlsplit(proxy_url)
            if not proxy_info.hostname:
                raise ValueError("malformed proxy url: {}".format(proxy_url))
            if not proxy_info.port:
                raise ValueError("port number required for proxy: {}".format(proxy_url))

            # SOCKS5 only: DNS queries should be performed on the remote side
            # (default behavior in "socks" module). Unfortunately, in practive,
            # that does not prevent DNS requests to be made outside of the SOCKS
            # tunnel as it would require monkey-patching the "socket" module and
            # would not work in some cases anyway.
            # More info: https://github.com/Anorov/PySocks/issues/22
            proxy_rdns = True

            # note to self: sockshandler.SocksiPyHandler is derived from
            # urllib.request.HTTPSHandler!!!
            own_handlers.append(sockshandler.SocksiPyHandler(
                        proxy_type, proxy_info.hostname, proxy_info.port,
                        proxy_rdns, proxy_info.username, proxy_info.password))

            got_socks_proxy = True
            break

        # Tests have shown that if mixed proxies are specified (i.e. "http" +
        # "https" + "socks") and there's a SOCKS proxy in the list, "SSL:
        # UNKNOWN_PROTOCOL" errors occur with HTTPS urls. As a result, when a
        # SOCKS proxy is specified, it must be the only proxy in the list.
        if not got_socks_proxy:
            own_handlers.append(urllib.request.ProxyHandler(proxies))

    if ssl_check_hostname is None:
        # allow user to override default behavior if needed
        ssl_check_hostname = kp.settings().get_bool(
                        "ssl_check_hostname", section="network", fallback=None)

    if ssl_check_hostname is not None:
        https_handler = _has_handler(urllib.request.HTTPSHandler)
        if https_handler is not None:
            if ssl_check_hostname:
                https_handler._context.check_hostname = True
                https_handler._context.verify_mode = ssl.CERT_REQUIRED
            else:
                https_handler._context.check_hostname = False
                https_handler._context.verify_mode = ssl.CERT_NONE
        else:
            ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            if ssl_check_hostname:
                # This is the default behavior when create_default_context() is
                # passed the SERVER_AUTH purpose.
                # "Explicit is better than implicit" (c)
                ssl_ctx.check_hostname = True
                ssl_ctx.verify_mode = ssl.CERT_REQUIRED
            else:
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
            own_handlers.append(urllib.request.HTTPSHandler(context=ssl_ctx))

    return UrllibOpener(urllib.request.build_opener(
                        *extra_pre_handlers, *own_handlers, *extra_handlers))

def proxies_to_dict(proxies):
    """
    Transform a list of proxy specification lines into a dictionary that is
    suitable to use with :py:func:`build_urllib_opener` and
    :py:mod:`urllib.request`.

    This function is used by :py:func:`build_urllib_opener` to parse
    Keypirinha's ``proxy`` global setting of the ``[network]`` section.

    *proxies* may be an iterable or a string, in which case it is split first
    using ``\\n`` as a separator and each line is trimmed with
    :py:meth:`str.strip`.

    Each entry of *proxies* must be a string that complies to the following
    grammar::

        prox_entry  ::= [ conn_scheme "=" ] proxy_url
        conn_scheme ::= ( "http" | "https" | "socks" | "socks4" | "socks5")
        proxy_url   ::= url_scheme "://" [ proxy_user ":" proxy_pass "@" ] netloc ":" proxy_port
        proxy_port  ::= unsigned

    If the ``conn_scheme`` part is not specified, ``url_scheme`` is assumed.

    Raises:
        ValueError: *proxies* cannot be parsed

    Note:
        If two proxies have the same scheme, the last one prevails.
    """
    if isinstance(proxies, str):
        proxies = proxies.split("\n")

    proxies_dict = {}
    for proxy_line in proxies:
        proxy_line = proxy_line.strip()
        if not proxy_line:
            continue

        proxy_pair = proxy_line.split("=", maxsplit=1)
        if len(proxy_pair) == 1:
            proxy_pair.insert(0, "")

        proxy_scheme = proxy_pair[0].strip().lower()
        proxy_url = proxy_pair[1].strip().lstrip("=").strip("/")

        # urlsplit() doesn't work well if no scheme is provided, try to
        # circumvent that first
        if "://" not in proxy_url:
            if not proxy_scheme:
                raise ValueError("missing scheme for proxy: {}".format(proxy_line))
            proxy_url = proxy_scheme + "://" + proxy_url

        proxy_info = urllib.parse.urlsplit(proxy_url)
        if not proxy_info.hostname or not proxy_info.scheme:
            raise ValueError("malformed proxy url: {}".format(proxy_line))
        if not proxy_info.port:
            raise ValueError("missing port number for proxy: {}".format(proxy_line))

        if not proxy_scheme:
            proxy_scheme = proxy_info.scheme.lower()

        # create/overwrite proxy entry by recomposing its url
        proxies_dict[proxy_scheme] = "{}://{}".format(
                                proxy_info.scheme.lower(), proxy_info.netloc)

    return proxies_dict
