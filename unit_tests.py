import unittest
from utilities.discord_transcriber import TranscriberBuilder

class TestDiarizedSingleFile(unittest.TestCase):
    def setUp(self):
        self.builder = TranscriberBuilder()
        return super().setUp()
    
    def test_10m_file():
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_30m_file():
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_60m_file():
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_10m_speaker_alignment():
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def test_30m_speaker_alignment():
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def test_60m_speaker_alignment():
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def tearDown(self):
        del self.builder
        return super().tearDown()
    
    if __name__ == "__main__":
        unittest.main()