def make_uncacheable(r):
    """
    Flags a response as uncacheable, e.g. animated images
    :param r: The original response
    :return: The modified response
    """
    if r.headers:
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers["Cache-Control"] = "public, max-age=0"
    return r
