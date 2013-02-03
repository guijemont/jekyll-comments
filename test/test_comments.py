from paste.fixture import TestApp
from nose.tools import *
from comments import app

class TestAddComment():
    correct_comment_params = {
        'author': "John Doe",
        'author_email': "john@example.com",
        'author_url': "http://www.example.com/",
        'content': """
        Oh hai!

        Nice post!

        John
        """,
        'post_id': "/2012/01/01/foo-bar",
        'return_url': "http://some-test-example-blog.com/blog/article1234"
    }
    def test_index(self):
        middleware = []
        testApp = TestApp(app.wsgifunc(*middleware))
        r = testApp.get('/', status=404)
        assert_equal(r.status, 404)

    def test_normal_post(self):
        middleware = []
        testApp = TestApp(app.wsgifunc(*middleware))

        r = testApp.post('/add_comment', params=self.correct_comment_params)
        assert_equal(r.status, 200)
        r.mustcontain("Thank you for your comment")
