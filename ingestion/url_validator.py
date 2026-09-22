import socket
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {
    'localhost', 'localhost.localdomain', '127.0.0.1', '0.0.0.0', '::1', '[::1]'
}

def is_valid_url(url: str) -> bool:
    """Basic syntax check for http/https URLs."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def is_ssrf_safe(url: str) -> bool:
    """
    Validates URL to prevent Server-Side Request Forgery (SSRF).
    Blocks private IP addresses, loopbacks, and link-local addresses.
    """
    if not is_valid_url(url):
        return False

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        hostname_lower = hostname.lower()
        if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith('.local') or hostname_lower.endswith('.internal'):
            return False

        # Attempt IP lookup
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return False
        except ValueError:
            # Hostname is a domain name, resolve IP
            try:
                ip_str = socket.gethostbyname(hostname)
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                    return False
            except socket.gaierror:
                # DNS failure or unresolvable
                pass

        return True
    except Exception:
        return False
