from typing import Iterable, List
import unittest

from parameterized import parameterized
import zopen
from zopen import PathLike


class TestZopen(unittest.TestCase):
    @parameterized.expand(
        [
            (["foo", "baz"], "bar", ["foo"], ["foo", "bar", "baz"]),
            (["foo", "baz"], "bar", None, ["bar", "foo", "baz"]),
            (["foo", "baz"], "foo", None, ["foo", "baz"]),
            (["foo", "baz"], "foo", ["foo"], ["foo", "baz"]),
            (["foo", "baz"], "baz", None, ["baz", "foo"]),
        ]
    )
    def test_get_new_mr_cache_lines(
        self,
        mr_docs: Iterable[PathLike],
        new_doc: PathLike,
        open_docs: Iterable[PathLike],
        expected: List[str],
    ) -> None:
        new_mr_cache_lines = zopen.get_new_mr_cache_lines(
            mr_docs, new_doc, open_docs
        )
        self.assertEqual(
            [str(mr_doc) for mr_doc in new_mr_cache_lines], expected
        )


if __name__ == '__main__':
    unittest.main()
