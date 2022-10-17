import shutil
from unittest import mock

import numpy as np
import pytest

from . import vl
from ...common.test_data import TestConstants
from ...emojistag import get_emoji
from ...imagestag import Colors
from ...logstag import VisualLog
from ...plotstag import Figure, MPLock


def test_basics_logging_methods():
    vl.test("Basic logging methods")
    vl.sub_test("Bullets")
    # logging mark down
    vl.md("* Just a list\n"
          "* of bullet\n"
          "* points")
    temp_path = vl.get_temp_path()
    assert len(temp_path)
    assert vl.get_temp_path("sub_path") == temp_path + "/sub_path"
    assert vl.load_ref("not_existing") is None
    vl.save_ref("example_ref", b"1234")
    assert vl.load_ref("example_ref") == b"1234"
    vl.sub_test("Titles and sub titles")
    # test title
    vl.checkpoint()
    vl.title("Title")
    vl.assert_cp_diff(hash_val="f8f23673dda04dd051c01f4c8cb95469")
    # test sub titles
    vl.checkpoint()
    vl.sub("A sub title")
    vl.sub_x3("Sub sub title")
    vl.sub_x4("Sub sub sub title")
    vl.assert_cp_diff(hash_val="bfdd65071e64655135ba6818ad1a60f5")
    vl.sub_test("Text and code")
    vl.checkpoint()
    vl.test("Just a piece of text")
    vl.code("How about a little bit of source code?")
    vl.assert_cp_diff(hash_val="e7fd24a8883dab906a2897fb7ab5266b")


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


def test_image():
    """
    Tests image logging
    """
    image_data = get_emoji(":deer:")
    image_data.convert("rgb", bg_fill=Colors.WHITE)
    # logging images
    vl.assert_image("stag",
                    source=image_data,
                    alt_text="An image of a stag - just because we can",
                    hash_val='4e5e428357fcf315f25b148747d633db',
                    scaling=0.5)
    vl.checkpoint()
    vl._log_images = False
    vl.image("an image which shouldn't get logged", image_data)
    vl._log_images = True
    vl.assert_cp_diff("d41d8cd98f00b204e9800998ecf8427e")
    # insert image via canvas
    vl.image("stag_canvas", source=image_data.to_canvas())
    # insert image via pixel data
    vl.image("stag_canvas", source=image_data.get_pixels())
    # test using general assert
    vl.assert_val("assert_stag", image_data,
                  hash_val='4e5e428357fcf315f25b148747d633db')
    with pytest.raises(AssertionError):
        vl.assert_val("assert_stag", image_data,
                      hash_val='4e5e428357fcf315f25b148747d633da')
    vl.checkpoint()
    vl._log_txt_images = False
    vl.sub_test("An image from the web scaled to 50%")
    vl.image("anotherStag", TestConstants.STAG_URL, scaling=0.5, download=False)
    vl.sub_test("An image from the web scaled to 50% w/ downloading")
    vl.image("anotherStag", TestConstants.STAG_URL, scaling=0.5, download=True)
    vl.sub_test("An image from the web scaled to 100%")
    vl.image("anotherStag", TestConstants.STAG_URL, scaling=1.0)
    vl._log_txt_images = True
    vl.assert_cp_diff(hash_val="8f6569634351a2e460ea40d018dd657a")
    # add image from bytes stream
    vl.sub_test("Logging an image provided as byte stream")
    vl.checkpoint()
    vl.image("image from byte stream", image_data.encode())
    vl.assert_cp_diff(hash_val="d55172dc8a0f239660274632c19cae1a")
    # insert image from web (as url)
    vl.image("Image link from URL", TestConstants.STAG_URL, download=False,
             scaling=0.5)
    # insert image from web (inserted)
    vl.image("Image download from URL", TestConstants.STAG_URL, download=True,
             scaling=0.5)


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
    vl.assert_val("test_dict", test_dict,
                  hash_val="95886f8348cd7b32465f9b96f32b232c")
    test_dict['child']['value'] = 456
    with pytest.raises(AssertionError):
        vl.assert_val("test_dict", test_dict,
                      hash_val="95886f8348cd7b32465f9b96f32b232c")


def test_figure():
    """
    Tests asserting figures
    """
    figure = Figure(cols=1)
    image_data = get_emoji(":deer:")
    figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.assert_val('figure_test', figure,
                  hash_val='b2927d2e8972b8a912e1155983f872be')
    with pytest.raises(AssertionError):
        vl.assert_val('figure_test', figure,
                      hash_val='d41d8cd98f00b204e9800998ecf8427c')
    plot = figure.add_plot().add_image(image_data, size_ratio=1.0)
    vl.assert_figure('test directly logging plot', plot,
                     hash_val='b2927d2e8972b8a912e1155983f872be')

    vl._log_images = False
    vl.figure("not_plotted_figure", plot)
    vl._log_images = True

    vl.sub_test("Logging figures created with matplotlib using add_matplot")
    np.random.seed(42)
    figure = Figure().borderless("plot")
    with figure.add_matplot(figsize=(4, 4)) as plt:
        plt.title("A grid with random colors")
        data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
        plt.imshow(data)
    vl.figure("random figure", figure)

    vl.sub_test("Logging figures created with matplotlib using MPLock()")
    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors")
        data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
        plt.imshow(data)
        vl.figure("random figure using MPLock", figure)

    vl.sub_test("Logging axes created with matplotlib using MPLock()")
    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors")
        np.random.seed(42)
        data = np.random.random_sample((16, 16, 3))
        axes = plt.imshow(data)
        vl.assert_figure("random figure using MPLock", axes,
                         hash_val="324a86b9b24b1fe1ff1d770cbc31e8e5")


def test_eval():
    """
    Tests evaluate
    """
    eval_data = vl.evaluate("4*5")
    assert eval_data == 20
    assert vl.evaluate("print('test123')") is None


def test_text():
    """
    Tests asserting text data
    """
    my_text = "Lorem ipsum"
    vl.assert_text("test_text", my_text,
                   hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c")
    vl.assert_val("test_text", my_text,
                  hash_val="0956d2fbd5d5c29844a4d21ed2f76e0c")
    with pytest.raises(AssertionError):
        vl.assert_text("test_text", my_text,
                       hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a")
    with pytest.raises(AssertionError):
        vl.assert_val("test_text", my_text,
                      hash_val="0956d2fbd5d5c29844a4d21ed2f76e0a")


def test_dataframe():
    """
    Tests dataframe logging
    """
    vl.test("Pandas DataFrame logging")
    # logging data frames
    import pandas as pd
    d = {'one': pd.Series([10, 20, 30, 40],
                          index=['a', 'b', 'c', 'd']),
         'two': pd.Series([10, 20, 30, 40],
                          index=['a', 'b', 'c', 'd'])}
    df = pd.DataFrame(d)
    vl.checkpoint()
    vl.sub_test("Logging a simple Pandas DataFrame")
    vl.df("A simple dataframe", df)
    vl.checkpoint()
    vl.assert_cp_diff(hash_val="d41d8cd98f00b204e9800998ecf8427e")
    vl.sub_test("HTML table printed w/o pretty html")
    vl._use_pretty_html_table = False
    vl.df("A simple dataframe w/o pretty html", df)
    vl._use_pretty_html_table = True
    vl.assert_cp_diff(hash_val="07b0542842e1799312fa83c2023279e2")

    # testing data frame assertion
    with mock.patch('builtins.print'):
        vl.assert_df("test_dataframe", df, dump=True)
    vl.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.assert_df("test_dataframe_no_data", df)
    vl.assert_val("test_dataframe", df)
    vl.assert_df("test_dataframe", df,
                 hash_val="914de108cea30eb542f1fb57dcb18afc")
    with pytest.raises(AssertionError):
        df.loc['a', 'one'] = 'NewValue'
        vl.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.assert_df("test_dataframe", df,
                     hash_val="914de108cea30eb542f1fb57dcb18afc")
    vl.sub_test("Log table without tabulate")
    vl._use_tabulate = False
    vl.df("DataFrame w/o tabulate", df)
    vl.sub_test("Log table without HTML")
    vl.markdown_html = False
    vl.df("DataFrame w/o tabulate", df)
    vl.markdown_html = True
    vl._use_tabulate = True
    vl.df("DataFrame w/o tabulate", df)
    vl._use_tabulate = True


def test_np_assert():
    """
    Tests numpy assertion
    """
    # testing numpy assertion
    np_array = np.ones((4, 4), dtype=float)
    with mock.patch('builtins.print'):
        vl.assert_np("test_np_array", np_array, dump=True)
    with pytest.raises(AssertionError):
        vl.assert_np("test_np_array_no_data", np_array)
    vl.assert_np("test_np_array", np_array, variance_abs=0.01)
    vl.assert_val("test_np_array", np_array)
    np_array[0][1] = 0.9999
    vl.assert_np("test_np_array", np_array, variance_abs=0.01)
    with pytest.raises(AssertionError):
        vl.assert_np("test_np_array", np_array, variance_abs=0.00001)
    with pytest.raises(AssertionError):
        np_array[0][1] = 0.9999
        vl.assert_np("test_np_array", np_array)

    with pytest.raises(NotImplementedError):
        vl.assert_np("test_np_array", np_array, hash_val="123")

    vl.assert_np("test_np_array", np_array, rounded=2,
                 hash_val="99140a9b8e68954a484e0de3c6861fc6")
    np_array[0][1] = 0.99
    vl.assert_np("test_np_array", np_array, rounded=2,
                 hash_val="99140a9b8e68954a484e0de3c6861fc6")
    np_array[0][1] = 0.98
    with pytest.raises(AssertionError):
        vl.assert_np("test_np_array", np_array, rounded=2,
                     hash_val="99140a9b8e68954a484e0de3c6861fc6")


def test_general_assertion():
    """
    Tests basic type assertion
    """
    with pytest.raises(NotImplementedError):
        vl.assert_val("abool", True)

    # logging images and figures:
    # Note: excessive amounts of tests for logging figures and images can
    # be found in the tests for plotstag
