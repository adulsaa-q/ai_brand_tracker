__version__ = "5.0.0"

# Load .env once, on first import of the package, without overriding anything the
# environment (or a test harness) has already set.
try:
    from dotenv import load_dotenv

    load_dotenv(override=False)
except ImportError:  # python-dotenv is a declared dep; tolerate its absence
    pass
