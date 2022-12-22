import os.path
import shutil
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
from ...imagestag import Color
from ...logstag import LogLevel
from ...logstag.console_stag import Console
from ...vislog import VisualLog
from ...plotstag import Figure, MPLock


def test_basics_logging_methods():
    vl.test.begin("Basic logging methods")
    vl.sub_test("Bullets")
    # logging mark down
    vl.md("* Just a list\n" "* of bullet\n" "* points")
    vl.md("* Just a list\n" "* of bullet\n" "* points", exclude_targets={"html", "md"})
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
    vl.test.assert_cp_diff(hash_val="86f74d4efab7c70690f1e86e9efec8dc")
    # test sub titles
    vl.test.checkpoint("log.subtitle")
    vl.sub("A sub title")
    vl.sub_x3("Sub sub title")
    vl.sub_x4("Sub sub sub title")
    vl.test.assert_cp_diff(hash_val="e69598020011731a12ae74e4d1a259e0")
    vl.sub_test("Text and code")
    vl.test.checkpoint("log.code")
    vl.test.begin("Just a piece of text")
    vl.code("How about a little bit of source code?")
    vl.hr()
    vl.page_break()
    vl.test.assert_cp_diff(hash_val="deb09ddaa3e0f23720a6536af11da0c9")
    assert not vl.target_log.is_micro


def test_add_and_links():
    """
    Tests the add and link functionalities
    :return:
    """
    vl.test.checkpoint("log.link")
    vl.link("SciStag", "https://github.com/scistag/scistag")
    vl.add("Test text")
    vl.add(123)
    vl.add(123.456)
    vl.add([123, 456])
    vl.add({"someProp": "someVal"})
    with pytest.raises(ValueError):
        vl.add(Color(22, 33, 44))
    with pytest.raises(ValueError):
        vl.add(b"12345")
    vl.test.assert_cp_diff(hash_val="d46775dc24d6c892a989c1e2481a7887")
    vl.test.checkpoint("log.link_adv")
    vl.link("Multiline\nLink", "https://github.com/scistag/scistag")
    vl.test.assert_cp_diff(hash_val="9ebcc1aada224b97a34d223ae5da4875")
    assert vl.max_fig_size.width > 100


def test_errors():
    """
    Provokes errors such as not existing prior log directories
    """
    try:
        shutil.rmtree("./logs/other")
    except FileNotFoundError:
        pass
    _ = VisualLog(target_dir="./logs/other", title="Just a test", clear_target_dir=True)


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
            "test_dict", test_dict, hash_val="95886f8348cd7b32465f9b96f32b232c"
        )


def test_figure():
    """
    Tests asserting figures
    """
    figure = Figure(cols=1)
    image_data = render_emoji(":deer:")
    figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_val(
        "figure_test", figure, hash_val="b2927d2e8972b8a912e1155983f872be"
    )
    with pytest.raises(AssertionError):
        vl.test.assert_val(
            "figure_test", figure, hash_val="d41d8cd98f00b204e9800998ecf8427c"
        )
    plot = figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_figure(
        "test directly logging plot", plot, hash_val="b2927d2e8972b8a912e1155983f872be"
    )

    vl.target_log.log_images = False
    vl.figure(plot, "not_plotted_figure")
    vl.target_log.log_images = True

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
        else "20ee5e3e393ec5099ec10273a838c263"
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
    with pytest.raises(AssertionError):
        vl.test.assert_text(
            "test_text", my_text, hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a"
        )
    with pytest.raises(AssertionError):
        vl.test.assert_val(
            "test_text", my_text, hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a"
        )


@patch("builtins.print")
def test_different_setups(_):
    """
    Tests different constructor settings
    """
    log: VisualLog = VisualLog(
        max_fig_size=(128, 128),
        log_to_disk=False,
        filetype=("jpg", 80),
        continuous_write=True,
    )
    assert not log.log_to_disk
    assert log.max_fig_size == (128, 128)
    assert log.image_format == "jpg" and log.image_quality == 80
    log.terminate()
    assert log._shall_terminate
    # TODO New log limit test with new component based approach
    #    log.set_log_limit(5)
    #    assert log._log_limit == 5
    #    assert log._log_stag[-1].log_limit == 5
    #    for content_count in range(7):
    #        log.default_builder.log("Test")
    #    assert len(log._logs["html"]) < 6

    log: VisualLog = VisualLog(
        max_fig_size=(128, 128),
        log_to_disk=False,
        filetype=("jpg", 80),
        continuous_write=True,
    )
    a_console = Console()
    log.add_console(a_console)
    log.default_builder.log("Console text")
    log.default_page.write_to_disk()
    log.flush()  # just another name for write_to_disk as of now
    assert log.default_page.get_page("wdwdd") == b""
    assert b"Console text" in log.default_page.get_body("html")
    assert log.default_page.get_body("wdwdd") == b""
    log.default_page.render(formats=None)  # enforce fetch
    log.default_page.write_to_disk(formats=None, render=False)

    # log without html
    no_html_log = VisualLog(formats_out={"txt"})
    no_html_log.default_page.write_html("shouldnt be logged")
    vl = no_html_log.default_builder
    vl.log("should be logged")
    with no_html_log as vl:
        vl.log("text")


def test_static_file():
    log: VisualLog = VisualLog(
        max_fig_size=(128, 128), log_to_disk=False, filetype=("jpg", 80)
    )
    log.add_static_file("testFile.bin", "bHello world")
    assert log.get_file("testFile.bin") == "bHello world"


def test_runner():
    """
    Tests running and looping functionality
    :return:
    """
    log: VisualLog = VisualLog(
        max_fig_size=(128, 128), log_to_disk=False, filetype=("jpg", 80)
    )
    assert not log.invalid
    log.invalidate()
    assert log.invalid


def test_statistics():
    """
    Tests the logging of statistics
    :return:
    """
    log: VisualLog = VisualLog(
        max_fig_size=(128, 128), log_to_disk=False, filetype=("jpg", 80)
    )
    log.default_builder.log_statistics()
    body = log.default_page.render().get_body("html")
    assert b"total updates" in body


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
    log = VisualLog(
        log_to_disk=True,
        target_dir=f"{bp}/clogs",
        clear_target_dir=True,
        formats_out={"html", "md"},
    )
    log.default_builder.log("Something")
    log.default_page.write_to_disk()
    data = log.get_file("index.md")
    assert log.get_file("../../evil/index.md") is None
    assert len(data) >= 5
    assert FilePath.exists(f"{bp}/clogs")
    new_log = VisualLog(
        log_to_disk=True,
        target_dir=f"{bp}/clogs",
        clear_target_dir=True,
        formats_out={"html", "md"},
    )
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
    log = VisualLog(
        log_to_disk=True,
        target_dir=f"{bp}/dlogs",
        formats_out={"html", "md", "txt"},
        continuous_write=True,
        log_to_stdout=True,
    )
    log.add_console(console)
    with mock.patch("builtins.print") as printer:
        log.default_page.write_html("<br>")
        log.default_page.write_txt("txt")
        log.default_page.write_md("md")
        assert printer.called
    log.default_page.render()


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
    vl.test.assert_cp_diff(hash_val="b4c6a2e280126abb4b4cd7361e2dd102")


def test_start_browser():
    """
    Tests the browser startup
    """
    with mock.patch("webbrowser.open") as open_browser:
        vis_log = VisualLog(start_browser=True, refresh_time_s=0.05)
        vis_log.run_server(test=True, show_urls=False)
        vis_log._start_app_or_browser(real_log=vis_log, url=vis_log.local_live_url)
        assert open_browser.called
    if (
        scistag.common.SystemInfo.os_type.is_windows
        or os.environ.get("QT_TESTS", "0") == "1"
    ):
        with mock.patch("webbrowser.open") as open_browser:
            vis_log = VisualLog(app="cute", refresh_time_s=0.05)
            vis_log.run_server(test=True, show_urls=False)
            assert not open_browser.called


def test_dependencies():
    """
    Tests dependency handling
    """
    vl.add_file_dependency("test.md")  # not yet implemented
