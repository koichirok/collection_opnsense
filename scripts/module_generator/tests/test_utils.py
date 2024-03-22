import unittest
from module_generator.utils import to_snake_case


class TestUtils(unittest.TestCase):
    def test_to_snake_case(self):
        # Test with title case input
        self.assertEqual(to_snake_case("SampleTitleCase"), "sample_title_case")

        # Test with camel case input
        self.assertEqual(to_snake_case("sampleCamelCase"), "sample_camel_case")

        # Test with hyphenated input
        self.assertEqual(to_snake_case("hyphenated-word"), "hyphenated_word")

        # Test with already snake case input
        self.assertEqual(to_snake_case("snake_case"), "snake_case")

        # Test with mixed case input
        self.assertEqual(to_snake_case("MixedCase-Word"), "mixed_case_word")

        # Test with numbers in input
        self.assertEqual(to_snake_case("Sample123Case"), "sample123_case")

        # Test with consecutive capital letters in input
        self.assertEqual(to_snake_case("SampleCAPSCase"), "sample_caps_case")

        # Test with consecutive capital letters and numbers in input
        self.assertEqual(to_snake_case("SampleCAPS123Case"), "sample_caps123_case")


if __name__ == "__main__":
    unittest.main()
