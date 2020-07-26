import unittest

import zopen


class TestZopen(unittest.TestCase):
    def test_get_new_mr_cache_lines(self) -> None:
        for mr_docs, new_doc, open_docs, expected in [
            (["foo", "baz"], "bar", ["foo"], ["foo", "bar", "baz"]),
            (["foo", "baz"], "bar", None, ["bar", "foo", "baz"]),
            (["foo", "baz"], "foo", None, ["foo", "baz"]),
            (["foo", "baz"], "foo", ["foo"], ["foo", "baz"]),
            (["foo", "baz"], "baz", None, ["baz", "foo"]),
        ]:
            with self.subTest(
                mr_docs=mr_docs,
                new_doc=new_doc,
                open_docs=open_docs,
                expected=expected,
            ):
                new_mr_cache_lines = zopen.get_new_mr_cache_lines(
                    mr_docs, new_doc, open_docs
                )
                self.assertEqual(
                    [str(mr_doc) for mr_doc in new_mr_cache_lines], expected
                )


if __name__ == '__main__':
    unittest.main()
