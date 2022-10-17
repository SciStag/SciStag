import codecs
import subprocess
import sys

from six import raise_from

import imgkit
from imgkit import from_file
from imgkit import from_url
from imgkit import from_string


def to_img(self, path=None):
    args = self.command(path)
    with subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as result:
        if self.source.isString() or (self.source.isFile() and self.css):
            charset_meta = '<meta charset="UTF-8">'
            string = (charset_meta + self.source.to_s()).encode("utf-8")
        elif self.source.isFileObj():
            string = self.source.source.read().encode("utf-8")
        else:
            string = None
        stdout, stderr = result.communicate(input=string)
        stderr = stderr.decode("utf-8") if stderr else ""
        exit_code = result.returncode
        if "cannot connect to X server" in stderr:
            raise OSError(
                f"{stderr}\n"
                'You will need to run wkhtmltoimage within a "virtual" X server.\n'
                "Go to the link below for more information\n"
                "http://wkhtmltopdf.org"
            )
        if "Error" in stderr:
            raise OSError("wkhtmltoimage reported an error:\n" + stderr)
        if exit_code != 0:
            xvfb_error = ""
            if "QXcbConnection" in stderr:
                xvfb_error = 'You need to install xvfb(sudo apt-get install xvfb, yum install xorg-x11-server-Xvfb, etc), then add option: {"xvfb": ""}.'
            raise OSError(
                f"wkhtmltoimage exited with non-zero code {exit_code}. error:\n{stderr}\n\n{xvfb_error}"
            )
        if "--quiet" not in args:
            sys.stdout.write(stderr)

        if not path:
            return stdout
        try:
            with codecs.open(path, mode="rb") as f:
                text = f.read(4)
                if text == "":
                    raise OSError(
                        "Command failed: {}\n"
                        "Check whhtmltoimage output without "
                        "'quiet' option".format(" ".join(args))
                    )
                return True
        except IOError as io_error:
            raise_from(
                OSError(
                    f"Command failed: {' '.join(args)}\n"
                    f"Check whhtmltoimage output without "
                    f"'quiet' option\n{io_error} "
                ),
                io_error,
            )


# Override erroneous original with our replacement
setattr(imgkit.IMGKit, "to_img", to_img)

__all__ = ["from_string", "from_url", "from_file"]
