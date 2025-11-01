import os
import unittest
from app import app, db
from app.models import User


class Phase0Test(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_readme_contains_move_plan(self):
        readme = os.path.join(os.getcwd(), 'README.md')
        self.assertTrue(os.path.exists(readme), 'README.md must exist')
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        self.assertTrue('MOVING_TO_BBC_PLAN.md' in content or '遷移計畫' in content,
                        'README should reference MOVING_TO_BBC_PLAN.md')

    def test_index_shows_latest_news_after_login(self):
        # create user
        u = User(username='t0', email='t0@example.com')
        u.set_password('test')
        db.session.add(u)
        db.session.commit()

        # login
        resp = self.client.post('/login', data={'username': 't0', 'password': 'test'}, follow_redirects=True)
        self.assertNotIn('/login', resp.request.path)

        # index
        resp2 = self.client.get('/')
        self.assertIn('Latest News', resp2.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
