import os
import unittest


class Phase4Test(unittest.TestCase):
    def test_seed_script_exists_or_note(self):
        path = os.path.join(os.getcwd(), 'scripts', 'seed_news.py')
        if not os.path.exists(path):
            self.skipTest('Seed script not implemented yet (scripts/seed_news.py)')
        # If exists, ensure file can be read
        with open(path, encoding='utf-8') as f:
            content = f.read()
        self.assertTrue(len(content) > 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
