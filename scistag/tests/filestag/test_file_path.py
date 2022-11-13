"""
Defines the tests for the FilePath class
"""

from scistag.common import WINDOWS
from scistag.filestag import FilePath


def test_filepath_basics():
    # Test file extension splitting
    assert FilePath.split_ext("test.png") == ("test", ".png")
    # Test directory name extraction
    assert FilePath.dirname("/home/user/file.txt") == "/home/user"
    # Test basename
    assert FilePath.basename("/home/user/file.txt") == "file.txt"
    # Test absolute path name resolving
    if WINDOWS:
        assert FilePath.absolute("C:/temp/../file.txt") == "C:/file.txt"
    else:
        assert FilePath.absolute("/home/user/../file.txt") == "/home/file.txt"
    # relative path
    assert FilePath.norm_path("home/user/../file.txt") == "home/file.txt"
    # Test relative absolute path
    assert FilePath.absolute_comb("test.txt",
                                  "/home/data/../") == "/home/test.txt"
    # Test relative absolute path to calling file
    if not WINDOWS:
        script_dir = FilePath.dirname(__file__)
        assert FilePath.absolute_comb(
            "__index__.py") == script_dir + "/" + "__index__.py"
        # caller's path
        assert FilePath.script_path() == script_dir
        # caller's script name
        assert FilePath.script_filename() == __file__
