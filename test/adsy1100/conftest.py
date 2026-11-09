import argparse
import fnmatch
import os
import re
import pytest
import iio

DEFAULT_XML_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "emu", "devices", "adsy1100.xml")
)


def pytest_addoption(parser):
    """Register command line options for IIO attribute testing."""
    def _add_safe(name, **kwargs):
        try:
            parser.addoption(name, **kwargs)
        except (ValueError, argparse.ArgumentError):
            pass

    _add_safe("--uri", default="", help="URI of the IIO context (e.g. ip:192.168.2.1)")
    _add_safe(
        "--iio-uri-override",
        default=os.environ.get("IIO_URI_OVERRIDE", ""),
        help="Bypass labgrid; direct libiio URI to point tests at (e.g. ip:192.168.2.1)",
    )
    _add_safe(
        "--iio-attr-category",
        default="all",
        choices=["all", "context", "device", "channel", "buffer", "debug"],
        help="Filter which attribute category to probe (default: all)",
    )
    _add_safe(
        "--iio-device-filter",
        default="",
        help="Glob/substring pattern to filter devices (e.g. *sniffer* or axi-ad9084*)",
    )
    _add_safe(
        "--iio-skip-attrs",
        default="",
        help="Comma-separated patterns of attribute names to skip (e.g. direct_reg_access,*sniffer*)",
    )
    _add_safe(
        "--iio-health-check",
        action="store_true",
        help="Probe context health after reading each attribute to immediately detect hangs/drops",
    )
    _add_safe(
        "--iio-mock-xml",
        default=DEFAULT_XML_PATH,
        help=f"Path to XML context when no hardware URI is supplied (default: {DEFAULT_XML_PATH})",
    )


@pytest.fixture(scope="session")
def resolved_iio_uri(request):
    """Determine the effective IIO URI across overrides, args, labgrid, and mock XML."""
    # 1. Direct CLI / env override
    override = request.config.getoption("--iio-uri-override") or os.environ.get(
        "IIO_URI_OVERRIDE"
    )
    if override:
        return override

    # 2. --uri option (from pytest-libiio or conftest)
    try:
        uri = request.config.getoption("--uri")
    except (ValueError, KeyError):
        uri = ""
    if uri:
        return uri

    # 3. Labgrid environment (if available)
    lg_env = os.environ.get("LG_ENV")
    if lg_env:
        try:
            from labgrid.environment import Environment
            from labgrid.strategy import Strategy

            env = Environment(lg_env)
            target = env.get_target("main")
            strategy = target.get_driver(Strategy)
            strategy.transition("shell")
            try:
                shell = target.get_driver("ADIShellDriver")
            except Exception:
                shell = target.get_driver("ShellDriver")

            out, _err, rc = shell.run(
                "ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1"
            )
            if rc == 0 and out and out[0].strip():
                return f"ip:{out[0].strip()}"
        except Exception as e:
            print(f"[conftest] Labgrid IP discovery failed: {e}")

    # 4. Fallback to mock XML if available
    mock_xml = request.config.getoption("--iio-mock-xml")
    if mock_xml and os.path.exists(mock_xml):
        return f"xml:{mock_xml}"

    return ""


@pytest.fixture(scope="session")
def iio_context(resolved_iio_uri):
    """Create and yield an iio.Context from the resolved URI."""
    if not resolved_iio_uri:
        pytest.skip(
            "No IIO URI provided and mock XML not found. Pass --uri, --iio-uri-override, or set LG_ENV."
        )

    uri = resolved_iio_uri
    if uri.startswith("xml:"):
        xml_path = uri[4:]
        ctx = iio.XMLContext(xml_path)
    else:
        ctx = iio.Context(uri)

    yield ctx
    del ctx


@pytest.fixture(scope="session")
def iio_filter_config(request):
    """Parse filtering and skip rules from pytest options."""
    category = request.config.getoption("--iio-attr-category") or "all"
    dev_filter = request.config.getoption("--iio-device-filter") or ""
    skip_raw = request.config.getoption("--iio-skip-attrs") or ""
    health_check = bool(request.config.getoption("--iio-health-check"))

    skip_patterns = [s.strip() for s in skip_raw.split(",") if s.strip()]

    def is_device_match(dev_name: str) -> bool:
        if not dev_filter:
            return True
        return fnmatch.fnmatch(dev_name.lower(), dev_filter.lower()) or (
            dev_filter.lower() in dev_name.lower()
        )

    def is_attr_skipped(attr_name: str) -> bool:
        for pat in skip_patterns:
            if fnmatch.fnmatch(attr_name.lower(), pat.lower()) or (
                pat.lower() in attr_name.lower()
            ):
                return True
        return False

    return {
        "category": category,
        "dev_filter": dev_filter,
        "skip_patterns": skip_patterns,
        "health_check": health_check,
        "is_device_match": is_device_match,
        "is_attr_skipped": is_attr_skipped,
    }
