import io
import os.path
import shutil
import time
from contextlib import redirect_stdout
from logging import ERROR
from sys import platform
from unittest import mock
from unittest.mock import patch

import numpy as np
import pytest

import scistag.common
from . import vl
from ...emojistag import render_emoji
from ...filestag import FilePath, FileStag
from ...imagestag import Color, Image
from ...logstag import LogLevel
from ...logstag.console_stag import Console
from ...vislog import VisualLog, HTMLCode, LogBuilder, cell
from ...plotstag import Figure, MPLock


def test_basics_logging_methods():
    vl.test.begin("Basic logging methods")
    vl.sub_test("Bullets")
    # logging mark down
    vl.test.checkpoint("md.logging")
    vl.md("* Just a list\n" "* of bullet\n" "* points").br(2)
    vl.md("* Just a list\n" "* of bullet\n" "* points").br(2)
    vl.md("* Just a list\n" "* of bullet\n" "* points", exclude_targets={"html", "md"})
    vl.title("test")
    vl.add_md("nothing_should_happen")
    vl.test.assert_cp_diff("c722c8d06a271fa356dcc3a7a67e5a1a")
    temp_path = vl.get_temp_path()
    assert len(temp_path)
    assert vl.get_temp_path("sub_path") == temp_path + "/sub_path"
    assert vl.test.load_ref("not_existing") is None
    vl.test.save_ref("example_ref", b"1234")
    assert vl.test.load_ref("example_ref") == b"1234"
    vl.sub_test("Titles and sub titles")
    # test title
    vl.test.checkpoint("log.title")
    vl.title("Title")
    vl.test.assert_cp_diff(hash_val="0a254eff1388eed0b1897ed647440b56")
    # test sub titles
    vl.test.checkpoint("log.subtitle")
    vl.sub("A sub title")
    vl.sub("Sub sub title", level=3)
    vl.sub("Sub sub sub title", level=4)
    with vl.sub():
        vl.add("Subtitle")
    vl.test.assert_cp_diff(hash_val="1d80d8e3c606ae88eef589018a0d3d38")
    vl.sub_test("Text and code")
    vl.test.checkpoint("log.code")
    vl.test.begin("Just a piece of text")
    vl.code("How about a little bit of source code?")
    vl.hr()
    vl.page_break()
    vl.test.assert_cp_diff(hash_val="60bd057930eba6c1913c786e46547cf2")
    assert not vl.is_micro


def test_add_and_links():
    """
    Tests the add and link functionalities
    :return:
    """
    vl.test.checkpoint("log.link")
    vl.link("https://github.com/scistag/scistag", "SciStag").br()
    vl.add("Test text", True)
    vl.add(123, br=True)
    vl.add(123.456, br=True)
    vl.add([123, 456], br=True)
    vl.add({"someProp": "someVal"}, br=True)
    with pytest.raises(ValueError):
        vl.add(b"12345", br=True)
    with pytest.raises(ValueError):
        test_image = Image(source=np.zeros((4, 4), dtype=np.uint8))
        stream = io.BytesIO()
        test_image.to_pil().save(stream, "tiff")
        vl.add(stream.getvalue(), br=True)
    vl.test.assert_cp_diff(hash_val="b159b391aa34ffb7006ebc8e39cf905c")
    vl.test.checkpoint("log.link_adv")
    vl.link("https://github.com/scistag/scistag", "Multiline\nLink").br()
    vl.test.assert_cp_diff(hash_val="c55363f81e747f8ff78bfcf84d8211ef")
    vl.test.checkpoint("callback")
    assert vl.max_fig_size.width > 100
    vl.add(lambda: vl.log("TestCall"))
    vl.add("**Bold**", mimetype="md").br()
    vl.add("<b>Bold</b>", mimetype="html").br()
    vl.test.assert_cp_diff("bab272087e9b7ae1453adc2b90c4316b")

    vl.test.checkpoint("add.womime")
    vl.add("A text", mimetype="notexisting")
    vl.test.assert_cp_diff("0639df408bd1a2d6fa8b8f4c072b6540")


def test_html():
    """
    Tests adding html
    """
    vl.test.checkpoint("logbuilder.html")
    vl.html("<b>A bold html text</b>")
    vl.html(HTMLCode("<b>Another bold html text</b>"))
    vl.test.assert_cp_diff("47c74d9c7b9aa67d16090caa0bcceabb")


def test_errors():
    """
    Provokes errors such as not existing prior log directories
    """
    try:
        shutil.rmtree("./logs/other")
    except FileNotFoundError:
        pass
    options = VisualLog.setup_options("disk")
    options.output.target_dir = "./logs/other"
    options.output.clear_target_dir = True
    options.page.title = "Just a test"
    _ = VisualLog(options=options)


def test_dict():
    """
    Tests the assertion of a dictionary
    """
    test_dict = {"child": {"value": 123}, "anotherValue": "Test"}
    vl.test.assert_val(
        "test_dict", test_dict, hash_val="95886f8348cd7b32465f9b96f32b232c"
    )
    test_dict["child"]["value"] = 456
    with pytest.raises(AssertionError):
        vl.test.assert_val(
            "test_dict", test_dict, hash_val="lockedc1b921dbe20fca8f1fc68543c3de55f3"
        )


def test_figure():
    """
    Tests asserting figures
    """
    figure = Figure(cols=1)
    image_data = render_emoji(":deer:")
    figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_val(
        "figure_test", figure, hash_val="a706d00b64ad66ad7009e32f0fcb8709"
    )
    with pytest.raises(AssertionError):  # Note: This test shall fail
        vl.test.assert_val(
            "figure_test", figure, hash_val="lockeda706d00b64ad66ad7009e32f0fcb8709"
        )
    plot = figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_figure(
        "test directly logging plot", plot, hash_val="a706d00b64ad66ad7009e32f0fcb8709"
    )

    vl.options.style.image.log_images = False
    vl.figure(plot, "not_plotted_figure")
    vl.options.style.image.log_images = True

    vl.sub_test("Logging figures created with matplotlib using add_matplot")
    np.random.seed(42)
    figure = Figure().borderless("plot")
    with figure.add_matplot(figsize=(4, 4)) as plt:
        plt.title("A grid with random colors")
        data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
        plt.imshow(data)
    vl.figure(figure, "random figure")

    vl.sub_test("Logging figures created with matplotlib using MPLock()")
    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors")
        data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
        plt.imshow(data)
        vl.figure(figure, "random figure using MPLock")

    hash_val = (
        "324a86b9b24b1fe1ff1d770cbc31e8e5"
        if platform == "darwin"
        else "927250f63394b0cab65e89714b986539"
    )
    # note minimal visualization differences between M1 Mac ons AMD64
    vl.sub_test("Logging axes created with matplotlib using MPLock()")
    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors")
        np.random.seed(42)
        data = np.random.random_sample((16, 16, 3))
        axes = plt.imshow(data)
        vl.test.assert_figure("random figure using MPLock", axes, hash_val=hash_val)


def test_eval():
    """
    Tests evaluate
    """
    eval_data = vl.evaluate("4*5")
    assert eval_data == 20
    assert vl.evaluate("print('', end='')") is None
    eval_data = vl.evaluate("4*4", log_code=False)
    assert eval_data == 16


def test_text():
    """
    Tests asserting text data
    """
    my_text = "Lorem ipsum"
    vl.test.assert_text(
        "test_text", my_text, hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c"
    )
    vl.test.assert_val(
        "test_text", my_text, hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c"
    )
    vl.hr()
    vl.log("Note: The following lines show a failed assertion on purpose for testing")
    with pytest.raises(AssertionError):  # Note: Shall fail
        vl.test.assert_text(
            "test_text", my_text, hash_val="locked0956d2fbd5d5c29844a4d21ed2f76e0c"
        )
    with pytest.raises(AssertionError):  # Note: Shall fail
        vl.test.assert_val(
            "test_text", my_text, hash_val="locked0956d2fbd5d5c29844a4d21ed2f76e0a"
        )
    vl.hr()
    vl.test.checkpoint("ML text")
    vl.test.begin("TextLogging")
    vl.hr()
    vl.text("Two lines\noftext", br=False)
    vl.text("Follow up")
    vl.hr()
    vl.text("Two lines\noftext", br=True)
    vl.text("Follow up")
    vl.hr()
    vl.text(123)
    vl.hr(title="This is a section")
    vl.test.assert_cp_diff("454ebc6a1a7f0227804cb7de2a1e67fe")


@patch("builtins.print")
def test_different_setups(_):
    """
    Tests different constructor settings
    """
    options = VisualLog.setup_options()
    options.style.image.max_fig_size = (128, 128)
    options.style.image.default_filetype = ("jpg", 80)
    log: VisualLog = VisualLog(options=options)
    assert not log.options.output.log_to_disk
    assert log.options.style.image.max_fig_size == (128, 128)
    assert log.options.style.image.default_filetype == ("jpg", 80)
    log.terminate()
    assert log._terminated
    # TODO New log limit test with new component based approach
    #    log.set_log_limit(5)
    #    assert log._log_limit == 5
    #    assert log._log_stag[-1].log_limit == 5
    #    for content_count in range(7):
    #        log.default_builder.log("Test")
    #    assert len(log._logs["html"]) < 6

    options = VisualLog.setup_options()
    options.style.image.max_fig_size = (128, 128)
    options.style.image.default_filetype = ("jpg", 80)
    log: VisualLog = VisualLog(options=options)
    a_console = Console()
    log.default_page.add_console(a_console)
    log.default_builder.log("Console text")
    log.default_page.write_to_disk()
    log.default_builder.flush()  # just another name for write_to_disk as of now
    assert log.default_page.get_page("wdwdd") == b""
    assert b"Console text" in log.default_page.get_body("html")
    assert log.default_page.get_body("wdwdd") == b""
    log.default_page.render(formats=None)  # enforce fetch
    log.default_page.write_to_disk(formats=None, render=False)

    # log without html
    options = VisualLog.setup_options()
    options.output.setup(formats={"txt"})
    no_html_log = VisualLog(options=options)
    no_html_log.default_page.write_html("shouldnt be logged")
    vl = no_html_log.default_builder
    vl.log("should be logged")
    with no_html_log as vl:
        vl.log("text")


def test_runner():
    """
    Tests running and looping functionality
    :return:
    """
    options = VisualLog.setup_options()
    options.style.image.max_fig_size = (128, 128)
    options.style.image.default_filetype = ("jpg", 80)
    log: VisualLog = VisualLog(options=options)
    assert not log.invalid
    log.invalidate()
    assert log.invalid


def test_simple_logging():
    """
    Tests the simple logging via info, critical etc.
    """
    log: VisualLog = VisualLog()
    cl = log.default_builder
    cl.test.begin("Basic logging methods")
    cl.log.info("Info text")
    cl.log.debug("Just a dev")
    cl.log.warning("Warning text")
    cl.log.error("Error text")
    cl.log.critical("Uh oh")
    cl.log("Direct logging")
    cl.log("This is an error", level=LogLevel.ERROR)
    cl.log("This is also an error", level="error")
    cl.log(None)
    vl.embed(log.default_page.render())


def test_adv_logging():
    """
    Tests the advanced logging methods which embed known patterns from
    a serial source
    """
    vl.test.begin("Advanced logging w/ tables")
    vl.log("|ColA|Colb|ColC|\n|1|2|3|", detect_objects=True)
    vl.br()
    vl.log(
        "With text before\n|ColA|Colb|ColC|\n|1|2|3|\nWith follow up text",
        detect_objects=True,
    )
    vl.br()
    vl.log("|ColA|Colb|ColC|\n|1|2|3|\nWith follow up text", detect_objects=True)


def test_clear_log():
    """
    Tests writing logs to disk and clearing the log directory
    """
    bp = os.path.dirname(__file__)
    try:
        shutil.rmtree(f"{bp}/clogs")
    except FileNotFoundError:
        pass
    options = VisualLog.setup_options()
    options.output.setup(
        disk=True,
        target_dir=f"{bp}/clogs",
        clear_target_dir=True,
        formats={"html", "md"},
    )
    log = VisualLog(options=options)
    log.default_builder.log("Something")
    log.default_page.write_to_disk()
    data = log.default_builder.service.get_file("index.md")
    assert log.default_builder.service.get_file("../../evil/index.md") is None
    assert len(data.body) >= 5
    assert FilePath.exists(f"{bp}/clogs")
    new_log = VisualLog(options=options)
    new_log.default_page.write_to_disk()
    data = FileStag.load(f"{bp}/clogs/index.md")
    assert len(data) <= 5


def test_printing():
    """
    Tests continuous printing and writing to disk
    """
    console = Console()
    console.progressive = True
    bp = os.path.dirname(__file__)
    options = VisualLog.setup_options("disk&console")
    options.output.target_dir = f"{bp}/dlogs"
    options.output.formats_out = {"html", "md", "txt"}
    log = VisualLog(options=options)
    log.default_page.add_console(console)
    std_out = io.StringIO()
    with redirect_stdout(std_out):
        with mock.patch("builtins.print") as printer:
            log.default_page.write_html("<br>")
            log.default_page.write_txt("txt")
            log.default_page.write_md("md")
            assert printer.called
            log.default_page.render()
            static_url = log.local_static_url
            assert static_url is None
            log.run(builder=lambda _: None)
            static_url = log.local_static_url
            assert static_url.startswith("file://")


def test_backup():
    """
    Tests creating and inserting backups
    """
    other_log = VisualLog()
    other_log.default_builder.log("Hello World")
    backup = other_log.default_builder.create_backup()
    vl.sub_test("inserting backups")
    vl.test.checkpoint("log.title")
    vl.insert_backup(backup)
    vl.test.assert_cp_diff(hash_val="23722b4bf72bb4a187341796c33834be")


def test_start_browser():
    """
    Tests the browser startup
    """
    with mock.patch("webbrowser.open") as open_browser:
        options = VisualLog.setup_options()
        options.run.setup(app_mode="browser", refresh_time_s=0.05)
        vis_log = VisualLog(options=options)
        with mock.patch.object(
            vis_log.default_builder.widget,
            "handle_event_list",
            lambda: time.time() + 0.01,
        ):
            vis_log.run_server(test=True, show_urls=False)
        vis_log._start_app_or_browser(real_log=vis_log, url=vis_log.local_live_url)
        assert open_browser.called
    with mock.patch("webbrowser.open") as open_browser:
        vis_log = VisualLog(options=options)
        vis_log.run_server(test=True, show_urls=False)
        vis_log._start_app_or_browser(real_log=vis_log, url=vis_log.local_live_url)
        assert open_browser.called
    if (
        scistag.common.SystemInfo.os_type.is_windows
        or os.environ.get("QT_TESTS", "0") == "1"
    ):
        options = VisualLog.setup_options()
        options.run.setup(app_mode="cute", refresh_time_s=0.05)
        with mock.patch("webbrowser.open") as open_browser:
            vis_log = VisualLog(options=options)
            vis_log.run_server(test=True, show_urls=False)
            assert not open_browser.called
        options.run.app_mode = "unknown"
        with mock.patch("webbrowser.open") as open_browser:
            with pytest.raises(ValueError):
                vis_log = VisualLog(options=options)
                vis_log.run_server(test=True, show_urls=False)


def test_dependencies():
    """
    Tests dependency handling
    """
    temp_path = vl.get_temp_path()
    os.makedirs(temp_path, exist_ok=True)
    fn = temp_path + "/test_markdown_dependency.md"
    FileStag.save_text(fn, text="DependsTest")
    with vl.cell.add():
        vl.data_loader.add_dependency(fn)
        assert vl.data_loader.get_hash(fn) is not None


def test_options():
    """
    Automatic option setup
    """
    tl = VisualLog(options="disk", debug=True)
    assert tl.options.output.log_to_disk


def test_continuous():
    """
    Tests continuous log
    :return:
    """
    options = VisualLog.setup_options()
    options.run.continuous = True

    class MyLog(LogBuilder):
        @cell
        def head(self):
            self.cache.inc("turns")
            if self["turns"] == 2:
                self.terminate()

    tl = VisualLog(options=options)
    tl.run(MyLog)
    tl = VisualLog(options=options)
    tl.run_server(MyLog, test=True)


def test_live_urls():
    """
    Tests the url provision
    """
    options = VisualLog.setup_options()
    tl = VisualLog(options=options)
    assert tl.local_live_url is None
    options = VisualLog.setup_options("server")
    tl = VisualLog(options=options)
    std_out = io.StringIO()
    with redirect_stdout(std_out):
        tl.run_server(test=True)
        assert tl.local_live_url is not None


def test_prepare():
    """
    Tests prepare_builder explicitly
    """
    options = VisualLog.setup_options()
    tl = VisualLog(options=options)
    with pytest.raises(TypeError):
        tl.prepare_builder(
            builder=str, page_session=tl.default_page, params={}, kwargs={}
        )
    tl._run_builder(builder=None)
    tl.run(builder=None)
