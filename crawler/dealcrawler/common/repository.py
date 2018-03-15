import threading


class Repository:

    def __init__(self, items, key_func):
        self.item_dict = {key_func(v): v for v in items}
        self.key_func = key_func
        self.item_access_lock = threading.RLock()

    # Thread safe operation
    def add_or_update_item(self, item):
        """
        Add or update item in memo repository.

        Notes: This operation is thread safe.
        :param item: data item.
        :return:
        """

        with self.item_access_lock:
            self.item_dict[self.key_func(item)] = item

    # Thread safe operation
    def get_item(self, key):
        """
        Get item in memo repository.

        Notes: This operation is thread safe.
        :param key: key to find the item.
        :return: item if found, otherwise None.
        """
        with self.item_access_lock:
            if key in self.item_dict:
                return self.item_dict[key]
            else:
                return None

    def all_items(self):
        return list(self.item_dict.values())
