import os
import base64
import hashlib


class DataLoaderMixin(object):
    data_directory = 'tests/data'

    def get_md5(self, content):
        return base64.encodestring(hashlib.md5(content).digest()).strip()

    def get_data_directory(self):
        return os.path.join(os.getcwd(), self.data_directory)

    def load_data(self, filename):
        path = os.path.join(self.get_data_directory(), filename)
        data = None
        with open(path) as fh:
            data = fh.read()
        return data
