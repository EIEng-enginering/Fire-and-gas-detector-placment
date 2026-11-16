import unittest
from fgmapping.theme import THEMES,contrast,stylesheet

class ThemeContract(unittest.TestCase):
    def test_colour_contrast(self):
        self.assertEqual(list(THEMES),['grey','dark','light'])
        for name,t in THEMES.items():
            with self.subTest(theme=name):
                for foreground in ('text','secondary'):
                    for background in ('cells','alternate','headers','window','buttons'):
                        self.assertGreaterEqual(contrast(t[foreground],t[background]),4.5,(name,foreground,background))
                self.assertGreaterEqual(contrast(t['selected_text'],t['selection']),4.5)
                self.assertGreaterEqual(contrast(t['selection'],t['cells']),3.0)
                self.assertGreaterEqual(contrast(t['border'],t['cells']),3.0)
                self.assertIn(t['window'],stylesheet(name))

if __name__=='__main__':unittest.main()
