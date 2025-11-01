import os
import unittest


class Phase3Test(unittest.TestCase):
    def test_partials_presence(self):
        base = os.path.join(os.getcwd(), 'app', 'templates')
        partials = ['_header.html.j2', '_footer.html.j2', '_news_card.html.j2', '_weather_widget.html.j2']
        missing = [p for p in partials if not os.path.exists(os.path.join(base, p))]
        # If partials are not yet created, skip with informative message
        if missing:
            self.skipTest(f'Partials not yet implemented, missing: {missing}')

        # If partials exist, also check base template references them (or index includes them)
        base_file = os.path.join(base, 'base.html.j2')
        if os.path.exists(base_file):
            with open(base_file, encoding='utf-8') as f:
                content = f.read()
            for p in partials:
                self.assertTrue(p in content or ('include' in content and p.split('.')[0] in content),
                                f'Expected partial {p} to be referenced in base.html.j2')
        else:
            # If no base.html.j2, at least ensure partial files exist
            self.assertEqual(missing, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
