version_info = (0, 17, 4)
__version__ = '.'.join(map(str, version_info))
try:
    from eventlet import greenpool
    GreenPool = greenpool.GreenPool

except ImportError as e:
    # This is to make Debian packaging easier, it ignores import
    # errors of greenlet so that the packager can still at least
    # access the version.  Also this makes easy_install a little quieter
    if 'greenlet' not in str(e):
        # any other exception should be printed
        import traceback
        traceback.print_exc()