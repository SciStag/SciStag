import shutil
from logging import ERROR
from unittest.mock import patch

import numpy as np
import pytest

from . import vl
from ...emojistag import render_emoji
from ...logstag import LogLevel
from ...logstag.console_stag import Console
from ...vislog import VisualLog
from ...plotstag import Figure, MPLock


def test_basics_logging_methods():
    vl.test.begin("Basic logging methods")
    vl.sub_test("Bullets")
    # logging mark down
    vl.md("* Just a list\n"
          "* of bullet\n"
          "* points")
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
    vl.test.assert_cp_diff(hash_val='f98803dc5b4000303ac0e223e354872d')
    assert not vl.target_log.is_micro


def test_errors():
    """
    Provokes errors such as not existing prior log directories
    """
    try:
        shutil.rmtree("./logs/other")
    except FileNotFoundError:
        pass
    _ = VisualLog(target_dir="./logs/other",
                  title="Just a test",
                  clear_target_dir=True)


def test_dict():
    """
    Tests the assertion of a dictionary
    """
    test_dict = {
        "child":
            {
                "value": 123
            },
        "anotherValue": "Test"
    }
    vl.test.assert_val("test_dict", test_dict,
                       hash_val="95886f8348cd7b32465f9b96f32b232c")
    test_dict['child']['value'] = 456
    with pytest.raises(AssertionError):
        vl.test.assert_val("test_dict", test_dict,
                           hash_val="95886f8348cd7b32465f9b96f32b232c")


def test_figure():
    """
    Tests asserting figures
    """
    figure = Figure(cols=1)
    image_data = render_emoji(":deer:")
    figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_val('figure_test', figure,
                       hash_val='b2927d2e8972b8a912e1155983f872be')
    with pytest.raises(AssertionError):
        vl.test.assert_val('figure_test', figure,
                           hash_val='d41d8cd98f00b204e9800998ecf8427c')
    plot = figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.test.assert_figure('test directly logging plot', plot,
                          hash_val='b2927d2e8972b8a912e1155983f872be')

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

    vl.sub_test("Logging axes created with matplotlib using MPLock()")
    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors")
        np.random.seed(42)
        data = np.random.random_sample((16, 16, 3))
        axes = plt.imshow(data)
        vl.test.assert_figure("random figure using MPLock", axes,
                              hash_val="20ee5e3e393ec5099ec10273a838c263")


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
    vl.test.assert_text("test_text", my_text,
                        hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c")
    vl.test.assert_val("test_text", my_text,
                       hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c")
    with pytest.raises(AssertionError):
        vl.test.assert_text("test_text", my_text,
                            hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a")
    with pytest.raises(AssertionError):
        vl.test.assert_val("test_text", my_text,
                           hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a")


@patch('builtins.print')
def test_different_setups(_):
    """
    Tests different constructor settings
    """
    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80),
                               continuous_write=True)
    assert not log.log_to_disk
    assert log.max_fig_size == (128, 128)
    assert log.image_format == "jpg" and log.image_quality == 80
    log.terminate()
    assert log._shall_terminate
    log.set_log_limit(5)
    assert log._log_limit == 5
    assert log._log_stag[-1].log_limit == 5
    for content_count in range(7):
        log.default_builder.log("Test")
    assert len(log._logs['html']) < 6

    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80),
                               continuous_write=True)
    a_console = Console()
    log.add_console(a_console)
    log.default_builder.log("Console text")
    log.write_to_disk()
    log.flush()  # just another name for write_to_disk as of now
    assert log.get_page("wdwdd") == b""
    assert b"Console text" in log.get_body("html")
    assert log.get_body("wdwdd") == b""
    log.render(formats=None)  # enforce fetch
    log.write_to_disk(formats=None, render=False)

    # log without html
    no_html_log = VisualLog(formats_out={"txt"})
    no_html_log.write_html("shouldnt be logged")
    vl = no_html_log.default_builder
    vl.log("should be logged")
    with no_html_log as vl:
        vl.log("text")


def test_static_file():
    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80))
    log.add_static_file("testFile.bin", "bHello world")
    assert log.get_file("testFile.bin") == "bHello world"


@patch('builtins.print')
def test_sub_logs(_):
    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80))
    log.default_builder.log("MainLog")
    log.begin_sub_log("SubLogA")
    log.default_builder.log("SubLogA")
    log.end_sub_log()
    log.begin_sub_log("SubLogB", max_fig_size=(128, 128))
    log.default_builder.log("SubLogB")
    log.end_sub_log()
    assert b"SubLogA" in log.sub_log_data["SubLogA"]["html"]
    assert b"SubLogB" in log.sub_log_data["SubLogB"]["html"]


def test_runner():
    """
    Tests running and looping functionality
    :return:
    """
    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80))
    assert log.invalid == False
    log.invalidate()
    assert log.invalid


def test_statistics():
    """
    Tests the logging of statistics
    :return:
    """
    log: VisualLog = VisualLog(max_fig_size=(128, 128), log_to_disk=False,
                               image_format=("jpg", 80))
    log.default_builder.log_statistics()
    body = log.render().get_body("html")
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
    vl.embed(log.render())


def test_adv_logging():
    """
    Tests the advanced logging methods which embed known patterns from
    a serial source
    """
    vl.test.begin("Advanced logging w/ tables")
    vl.log("|ColA|Colb|ColC|\n|1|2|3|", detect_objects=True)
    vl.br()
    vl.log("With text before\n|ColA|Colb|ColC|\n|1|2|3|\nWith follow up text",
           detect_objects=True)
    vl.br()
    vl.log("|ColA|Colb|ColC|\n|1|2|3|\nWith follow up text",
           detect_objects=True)
