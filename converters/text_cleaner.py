import re
from typing import Optional


class TextCleaner:

    """ Clearing strings from unwanted symbols """

    @staticmethod
    def clear_string(string_to_clean: str, symbols_to_clean: tuple) -> Optional[str]:
        """ Removing unwanted symbols from string """
        if string_to_clean:
            for symbol in symbols_to_clean:
                re_filter = re.compile(symbol)
                if symbol == "<br /><br />":
                    string_to_clean = re.sub(re_filter, r'\n', string_to_clean)
                elif symbol == 'quot;':
                    string_to_clean = re.sub(re_filter, '"', string_to_clean)
                else:
                    string_to_clean = re.sub(re_filter, '', string_to_clean)
            return string_to_clean

    @staticmethod
    def get_number_from_string(string_to_parse: Optional[str]) -> Optional[float]:
        """ From "<b>Budget</b>: $1,000<br/>" to 1000 """

        if string_to_parse:
            number = ""
            for char in string_to_parse:
                if char.isnumeric() or char == ".":
                    number += char
            return float(number)

    @staticmethod
    def replace_field_from_string(string_to_clean: str, fields_to_replace: tuple) -> str:
        """ From "<b>Category</b>: Full Stack Development<br /><b>" to "Full Stack Development" """

        for field in fields_to_replace:
            string_to_clean = string_to_clean.replace(field, "")
        return string_to_clean
