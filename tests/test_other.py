import unittest
from html.parser import HTMLParser

from utils.other import truncate_html


class StrictHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)

    def handle_endtag(self, tag):
        self.assert_tag(tag)

    def assert_tag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise AssertionError(f"Unbalanced tag: {tag}")


class TruncateHTMLTests(unittest.TestCase):
    def test_closes_tags_after_truncation(self):
        result = truncate_html("<b>" + "x" * 1100 + "</b>", 1024)
        parser = StrictHTMLParser()
        parser.feed(result)
        parser.close()

        self.assertLessEqual(len(result), 1024)
        self.assertEqual(parser.stack, [])
        self.assertTrue(result.endswith("...</b>"))

    def test_does_not_cut_an_entity(self):
        result = truncate_html("a" * 1018 + "&amp;tail", 1024)

        self.assertLessEqual(len(result), 1024)
        self.assertNotIn("&am...", result)


if __name__ == "__main__":
    unittest.main()
