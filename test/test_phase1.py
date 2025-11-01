import os
import unittest
from app import app, db
from app.models import User


class Phase1Test(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_article_templates_exist(self):
        base = os.path.join(os.getcwd(), 'app', 'templates')
        # Phase1 requirement changed: Article templates should NOT exist (replaced by category templates)
        present = []
        for name in ['ArticleA.html.j2', 'ArticleB.html.j2', 'ArticleC.html.j2', 'ArticleD.html.j2', 'ArticleE.html.j2', 'ArticleF.html.j2']:
            path = os.path.join(base, name)
            if os.path.exists(path):
                present.append(name)
        self.assertEqual(present, [], f'Article templates should not exist; found: {present}')

    def test_article_routes_render_and_have_title(self):
        # create and login user
        u = User(username='phase1', email='phase1@example.com')
        u.set_password('test')
        db.session.add(u)
        db.session.commit()
        login_resp = self.client.post('/login', data={'username': 'phase1', 'password': 'test'}, follow_redirects=True)
        self.assertNotIn('/login', login_resp.request.path)

        routes = ['/ArticleA', '/ArticleB', '/ArticleC', '/ArticleD', '/ArticleE', '/ArticleF']
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f'{r} did not return 200')
            html = resp.get_data(as_text=True)
            # check there's a title or h1 in the returned HTML
            self.assertTrue('<title>' in html or '<h1>' in html or '<h2>' in html, f'{r} has no obvious title/header')


if __name__ == '__main__':
    unittest.main(verbosity=2)
