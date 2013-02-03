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

    def test_size(self):
        middleware = []
        testApp = TestApp(app.wsgifunc(*middleware))

        comment_params = dict(self.correct_comment_params)
        comment_params['content'] = "a" * 100000

        r = testApp.post('/add_comment', params=comment_params)
        assert_equal(r.status, 200)
        r.mustcontain("Thank you for your comment")

        comment_params['content'] = "a" * 102400
        with assert_raises(ValueError):
            testApp.post('/add_comment', params=comment_params, expect_errors=True)
