import os
import unittest
from app import app, db
from app.models import User, Article


class Phase2Test(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_article_model_and_detail_route(self):
        # create user/author
        u = User(username='phase2', email='phase2@example.com')
        u.set_password('test')
        db.session.add(u)
        db.session.commit()

        # create article
        a = Article(headline='Test Article', summary='Sum', body='Body', author_id=u.id)
        db.session.add(a)
        db.session.commit()

        # login
        login_resp = self.client.post('/login', data={'username': 'phase2', 'password': 'test'}, follow_redirects=True)
        self.assertNotIn('/login', login_resp.request.path)

        # fetch article detail
        resp = self.client.get(f'/article/{a.id}')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('Test Article', html)

    def test_migration_file_exists(self):
        path = os.path.join(os.getcwd(), 'migrations', 'versions', 'cc3a9f4b7a2a_add_article_model.py')
        self.assertTrue(os.path.exists(path), 'Expected migration file for article model to exist')


if __name__ == '__main__':
    unittest.main(verbosity=2)
