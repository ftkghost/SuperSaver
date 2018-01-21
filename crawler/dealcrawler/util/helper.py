def sanitize_price(price_str):
    """
    Normalise a price string and convert to float value.
    :param price_str: Price string to normalise.
    :return: Float price value.
    """
    if price_str is None:
        return None
    price_str = price_str.strip('$ \t\n\r')
    price_str = price_str.replace(',', '')
    return float(price_str)


def substr_surrounded_by_chars(full_str, char_pair, offset=0):
    """
    Extract substring surrounded by open & close chars.
    For example, 'value: { k1: v1, k2: v2 }'
    :param full_str: target string.
    :param char_pair: a tuple contains open & close tag.
    :param offset: Start point to search substring.
    :return: Substring which include open & close char.
    """
    open_tag, close_tag = char_pair
    if len(full_str) <= offset or len(full_str) < 2:
        raise ValueError('Invalid offset value.')
    if len(open_tag) != 1 and len(close_tag) != 1:
        raise ValueError('Invalid close tag characters, open & close tag length must be 1.')
    stack = []
    open_index = -1
    close_index = -1
    for i in range(offset, len(full_str)):
        ch = full_str[i]
        if ch == open_tag:
            if open_index == -1:
                open_index = i
            stack.append(ch)
        elif ch == close_tag:
            if len(stack) < 1:
                raise ValueError("Invalid str value, close tag before open tag")
            stack.pop()
            if len(stack) == 0:
                close_index = i
                break
    if len(stack) > 0:
        raise ValueError('Invalid str value, open tag and close tag are not paired.')
    return full_str[open_index:close_index + 1]


def extract_values_with_xpath(selector, xpath_string, func=str.strip):
    """
    Extract all values with Selector.xpath() and process each of them with func.
    @selector: this is Selector instance method first argument (self).
    @xpath_string: css string pass to Selector.xpath().
    @func: function at least accepts 1st string argument.(or other arguments has default value)
    @default: default value if there is no result from Selector.xpath()
    Return a processed value returned from @func.
    """
    results = selector.xpath(xpath_string)
    if results is None or len(results) == 0:
        return
    for r in results.extract():
        if func is None:
            yield r
        else:
            yield func(r)


def extract_first_value_with_xpath(selector, xpath_string, func=str.strip, default=None):
    """
    Extract first value with Selector.xpath()
    @selector: this is Selector instance method first argument (self).
    @xpath_string: css string pass to Selector.xpath().
    @func: function at least accepts 1st string argument.(or other arguments has default value)
    @default: default value if there is no result from Selector.xpath()
    return a processed value returned from @func.
    """
    results = selector.xpath(xpath_string)
    if results is None or len(results) == 0:
        return default
    else:
        if func is None:
            return results[0].extract()
        else:
            return func(results[0].extract())


def extract_values_with_css(selector, css_string, func=str.strip):
    """
    Extract all values with Selector.css() and process each of them with func.
    @selector: this is Selector instance method first argument (self).
    @css_string: css string pass to Selector.css().
    @func: function at least accepts 1st string argument.(or other arguments has default value)
    @default: default value if there is no result from Selector.css()
    Return a processed value returned from @func.
    """
    results = selector.css(css_string)
    if results is None or len(results) == 0:
        return
    for r in results.extract():
        if func is None:
            yield r
        else:
            yield func(r)


def extract_first_value_with_css(selector, css_string, func=str.strip, default=None):
    """
    Extract first value with Selector.css() and process it with func.
    @selector: this is Selector instance method first argument (self).
    @css_string: css string pass to Selector.css().
    @func: function at least accepts 1st string argument.(or other arguments has default value)
    @default: default value if there is no result from Selector.css()
    Return a processed value returned from @func.
    """
    results = selector.css(css_string)
    if results is None or len(results) == 0:
        return default
    else:
        if func is None:
            return results[0].extract()
        else:
            return func(results[0].extract())


def first_elem_with_xpath(selector, xpath):
    results = selector.xpath(xpath)
    if results is None:
        return None
    for elem in results:
        return elem
    return None


def first_elem_with_css(selector, css):
    results = selector.css(css)
    if results is None:
        return None
    for elem in results:
        return elem
    return None


def exists_elem_with_xpath(selector, xpath, expected_value=None, comparer=None):
    results = selector.xpath(xpath)
    if results is None or len(results) == 0:
        return False
    if expected_value is None:
        return True
    for value in results.extract():
        comp_result = (value == expected_value)
        if comparer is not None:
            comp_result = comparer(value, expected_value)
        if comp_result:
            return True
    return False
