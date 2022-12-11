import os
import fnmatch
from stat import S_ISDIR
from typing import List


class GitScanner:
    """
    Scans a git repository and creates a list of non-ignored files and their size.

    This is used in the unit test to verify no garbage is committed into the repo.

    Note that this class is a very minimalistic approach for a coarse validity check and does not
    fulfill all git standards ignore masks etc. So feel free to use this class but don't complain ;).
    """

    def __init__(self):
        """
        Initiailizer
        """
        self.total_size = 0
        "The count of valid directories"
        self.file_count = 0
        "The count of valid files"
        self.dir_count = 0
        "The count of directories"
        self.dir_list: list[dict] = []
        """The list of all directories parsed. Format: {"path": path, "ignored": false}. Note that only the highest
        'level ignored directories will be listed, not the nested ones."""
        self.file_list: list[dict] = []
        'The list of all non ignored files. Format: {"filename": name, "size": size_in_bytes}'
        self.file_list_by_size: list[dict] = []
        'The list of all non ignored files by size. Format: {"filename": name, "size": size_in_bytes}'

    @classmethod
    def get_is_ignored(cls, name: str, is_dir: bool, ignore_list: list[str]):
        """
        Check is a given name is ignored
        :param name: The file or directory name
        :param is_dir: Is  the element a directory?
        :param ignore_list: The ignore list
        :return: True if the element shall be ignored
        """
        for element in ignore_list:
            if "dart_tool" in element and "dart_tool" in name:
                pass
            if element.endswith("/"):
                if is_dir and fnmatch.fnmatch(name, element[0:-1]):
                    return True
            else:
                if fnmatch.fnmatch(name, element):
                    return True
        return False

    @classmethod
    def add_git_ignore(cls, base_path, org_list: list[str], filename: str) -> list[str]:
        """
        Creates an update gitignore mask list for the current directory
        :param base_path: The base path we are starting in
        :param org_list: The previous ignore list
        :param filename: The path of the .gitignore file
        :return:
        """
        with open(filename, "r") as ignore_file:
            all_lines = ignore_file.readlines()
            all_lines = [
                element.rstrip("\n")
                for element in all_lines
                if not element.startswith("#")
            ]
            all_lines = [element for element in all_lines if not len(element) == 0]
            all_lines = [
                os.path.normpath(f"{base_path}/{element}")
                if element.startswith("/")
                else f"*/" + element
                for element in all_lines
            ]
            return org_list + all_lines

    @classmethod
    def find_valid_repo_files(
        cls, path: str, file_list: List, ignore_list: List, dir_list: List
    ) -> None:
        """
        Finds a list of valid files in the current directory. Continues the search in subdirectories
        :param path: The base path
        :param file_list: The current list of file
        :param ignore_list: The ignore list
        :param dir_list: The list of parsed directories
        """
        cur_content = os.listdir(path)
        git_ignore_path = f"{path}/.gitignore"
        if os.path.exists(git_ignore_path):
            ignore_list = cls.add_git_ignore(path, ignore_list, git_ignore_path)
        for cur_element in cur_content:
            full_path = os.path.normpath(f"{path}/{cur_element}")
            cur_stat = os.stat(full_path)
            is_dir: bool = S_ISDIR(cur_stat.st_mode)
            is_ignored = cls.get_is_ignored(
                full_path, is_dir=is_dir, ignore_list=ignore_list
            )
            if is_dir:
                dir_list.append({"path": full_path, "ignored": is_ignored})
            if not is_ignored:
                if is_dir:
                    cls.find_valid_repo_files(
                        full_path, file_list, ignore_list, dir_list=dir_list
                    )
                else:
                    file_list.append({"filename": full_path, "size": cur_stat.st_size})

    @classmethod
    def compute_total_size(cls, filelist: List) -> int:
        """
        Computes the total size of the non ignored files
        :param filelist: The list of files
        :return: The size in bytes
        """
        total_size = 0
        for element in filelist:
            total_size += element["size"]
        return total_size

    def scan(self, path: str):
        """
        Executes a scan on given base directory. The results are stored in the member variables of this object
        (.file_list, .total_sub_node_count etc.)
        :param path: The repository base path
        """
        res_file_list = []
        cur_ignore_list = ["*/.git/*"]
        self.dir_list.clear()
        self.find_valid_repo_files(
            path, res_file_list, ignore_list=cur_ignore_list, dir_list=self.dir_list
        )
        self.total_size = self.compute_total_size(res_file_list)
        self.file_list = res_file_list
        res_file_list = sorted(res_file_list, key=lambda x: x["size"], reverse=True)
        self.dir_count = len(self.dir_list)
        self.file_count = len(self.file_list)
        self.file_list_by_size = res_file_list

    def get_large_files(
        self, min_size: int, ignore_list: list[str], hard_limit_size: int = -1
    ) -> list[str]:
        """
        Returns all files larger than a given threshold which are not on the ignore list
        :param min_size: The minimum size in bytes
        :param hard_limit_size: If this size is exceeded even files on the ignore list will not be ignored. -1 if there
        is no hard limit.
        :param ignore_list: Masks of the files to ignore
        :return: The list of all remaining files
        """
        large_elements = [
            element for element in self.file_list if element["size"] >= min_size
        ]
        result_list: list[str] = []
        for element in large_elements:
            skip = False
            if hard_limit_size == -1 or element["size"] < hard_limit_size:
                for ignore_entry in ignore_list:
                    if fnmatch.fnmatch(element["filename"], ignore_entry):
                        skip = True
                        break
            if skip:
                continue
            else:
                result_list.append(element["filename"])
        return result_list
