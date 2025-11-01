import os
import unittest


class Phase5Test(unittest.TestCase):
    def test_init_db_route_presence(self):
        routes = os.path.join(os.getcwd(), 'app', 'routes.py')
        self.assertTrue(os.path.exists(routes), 'app/routes.py must exist')
        with open(routes, encoding='utf-8') as f:
            content = f.read()
        # Phase5 requirement: /init_db route should NOT be present in production-oriented design
        self.assertNotIn('/init_db', content, '/init_db route should be removed or protected for production')


if __name__ == '__main__':
    unittest.main(verbosity=2)
