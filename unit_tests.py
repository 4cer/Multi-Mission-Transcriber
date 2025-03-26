import unittest
from utilities.discord_transcriber import TranscriberBuilder
from utilities.strategies.output_strategy import OutputFormatStrategyFactory
from utilities.prompt_builder import PromptBuildStrategyFactory

class TestPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.factory = PromptBuildStrategyFactory
        return super().setUp()
    
    def test_string(self):
        string = "This is an example prompt. Nothing really to see."

        builder = self.factory.get_strategy('str')
        outputa = builder.build(string)
        self.assertEqual(string, outputa)

        builder = self.factory.get_strategy('string')
        outputb = builder.build(string)
        self.assertEqual(string, outputb)

    def test_dictionary(self):
        expected = "Test D&D session recording. Deities:Ragnar,Rognar,Rodgins. Places:Goria,Rivendel. Gloria:Mortis,Victis. Characters:Test Tost,Riggurd,Ricky Van Halen. And that's it, folks!"
        dictionary = {
            'prefix': 'Test D&D session recording.',
            'suffix':"And that's it, folks!",
            'Deities': ['Ragnar', 'Rognar', 'Rodgins'],
            'Places': ['Goria','Rivendel'],
            'Gloria': ['Mortis', 'Victis'],
            'Characters': ['Test Tost', 'Riggurd', 'Ricky Van Halen']
        }

        builder = self.factory.get_strategy('dict')
        outputa = builder.build(dictionary)
        self.assertEqual(expected, outputa)

        builder = self.factory.get_strategy('dictionary')
        outputb = builder.build(dictionary)
        self.assertEqual(expected, outputb)

    def test_directory(self):
        # expected = "Nagranie sesji gry Warhammer Fantasy 2e zawierające fantastyczne nazwy i zapożyczenia z języka niemieckiego. Bóstwa:Sigmar,Ursun,Morr,Shallya,Taal,Rhya,Ulric,Verena,Ranald,Manann,Myrmidia,Grimnir,Grungni,Valaya,Nakai,Morag-heg,Khaine,Asuryan,Kurnous,Isha,Chotec,Tepok,Tzunki,Itzl,Quetzl,Gork,Mork,Khorne,Nurgle,Slaanesh,Tzeentch,Hashut,Kweethul. Miejsca:Kislev,Ostermark,Rhebulas,Sitlakes,Menshenfresserhoffen,Biersalhof,Leszken,Bissendorf,Kiel,Seuthes,Trautenau,Tauer,Zeisholz,Brunfahre,Brunwasser,Rundespitze,Weiler,Nagenhof,Osterwald,Eisental,Mielau,Nachtdorf,Blutfurt,Fichtetal,Burgenhof,Rheden,Fortenhaf,Gerdouen,Bechafen,Dorna. Narodowości:Strzyganka,Strzyganin. Postaci:Aurelio Viermetz,Balthasar Eisenhart,Berthold Krüger,Hans Bauermann,Otto Lustig,Siegfried Stroheim,Lorenz Geißelbruder,Matthias Krähenfels. Software:Foundry VTT,Craig,Giarc."
        expected = "Test prefix, ends with a period. A:Something,Nothing. Ba:Some space?,Zażółć Gęślą Jaźń,Porrito. Just something."

        directory = r'prompt\testA'

        builder = self.factory.get_strategy('dir')
        outputa = builder.build(directory)
        self.assertEqual(expected, outputa)

        builder = self.factory.get_strategy('directory')
        outputb = builder.build(directory)
        self.assertEqual(expected, outputb)
    
    def tearDown(self):
        del self.factory
        return super().tearDown()
    
class TestOutputStrategy(unittest.TestCase):
    def setUp(self):
        self.builder = OutputFormatStrategyFactory()
        self.segments = [
            {
                'start': None,
                'end': None,
                'speaker': 'Shopkeeper',
                'text': "You're not a cop, are you?"
            },
            {
                'start': None,
                'end': None,
                'speaker': 'The ruler of planet Omicron Persei 8',
                'text': "Oh you know... Just some guy... THERULEROFTHEPLANETOMICRONPERSEI8"
            },
            {
                'start': None,
                'end': None,
                'speaker': 'Shopkeeper',
                'text': "So what can I do you for?"
            }
        ]
        return super().setUp()
    
    def test_text(self):

        pass

    def test_dense(self):
        pass

    def test_raw(self):
        pass

    def test_json(self):
        pass
    
    def tearDown(self):
        del self.builder
        return super().tearDown()

class TestDiarizedSingleFile(unittest.TestCase):
    def setUp(self):
        self.builder = TranscriberBuilder()
        return super().setUp()
    
    def test_10m_file(self):
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_30m_file(self):
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_60m_file(self):
        # Criteria:
        # - doesn't crash
        # - produces expected speaker count
        raise NotImplementedError()
    
    def test_10m_speaker_alignment(self):
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def test_30m_speaker_alignment(self):
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def test_60m_speaker_alignment(self):
        # Criteria:
        # - accuracy 90%+
        raise NotImplementedError()
    
    def tearDown(self):
        del self.builder
        return super().tearDown()
    
if __name__ == "__main__":
    unittest.main(failfast=False)