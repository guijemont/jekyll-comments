#!/usr/bin/env python
"""
CGI script that takes takes a POST to the address ./add_comment (normally from
a comment form) and sends that comment formatted in yaml to the email address
set in COMMENT_EMAIL.

The resulting yaml file is meant to be used with Jekyll::StaticComments. See
https://github.com/mpalmer/jekyll-static-comments/
http://theshed.hezmatt.org/jekyll-static-comments/
"""

import web
import cgi
import time
import os, os.path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# config
COMMENT_EMAIL = "blog@example.com"
FROM_EMAIL = "noreply@example.com"
MAX_SIZE = 1024
MAX_SIZE_COMMENT = 102400

URLS = (
    '/add_comment', 'CommentHandler'
)

def is_test():
    """
    Returns true iff the environment variable WEBPY_ENV is set to "test".
    """
    webpy_env = os.environ.get('WEBPY_ENV', '')
    return webpy_env == 'test'

# pylint: disable=W0232
# no __init__ because we only provide methods
class CommentHandler:
    """
    Class meant to be used by web.py.
    Handles POST requests in the POST method
    """
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    ACK_MSG = """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
       "http://www.w3.org/TR/html4/strict.dtd">
    <html>
        <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            <meta http-equiv="refresh" content="5;url=%(return_url)s" />
            <title>Comment Received</title>
        </head>
    <body>
    <h1>Comment Received</h1>
        <p>Thank you for your comment. It will be reviewed and published shortly.</p>
        <p>You are now returning to the page you were on. Click the link if you are not redirected automatically.</p>
        <p><a href="%(return_url)s">%(return_url)s</a></p>
    </body>
    </html>
    """
    ERROR_MSG = """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
       "http://www.w3.org/TR/html4/strict.dtd">
    <html>
        <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            <title>Problem with input</title>
        </head>
    <body>
    <h1>Error!</h1>
        <p>The following error was detected: <br/>
        %(error_msg)
        </p>
    </body>
    </html>
    """
    SMTPCONF = {
        'host': 'localhost',
        'port': 1025
    }
    # pylint: disable=C0103
    # name isn't nice, but that's web.py's API
    def POST(self):
        """
        Handle a POST request: gets its content, transforms it into yaml, email
        the result and returns a confirmation page.
        """
        try:
            input_ = web.input()
        except ValueError:
            referer = web.ctx.env.get('HTTP_REFERER', '/')
            return self.ERROR_MSG % {
                'error_msg': "Input is too big, you should write less! Hit the"
                    " back button and try again.",
                'return_url': referer
            }
        comment = {
            'author_ip': web.ctx.ip,
            'date_gmt': time.strftime(self.DATE_FORMAT, time.gmtime()),
            'date': time.strftime(self.DATE_FORMAT, time.localtime())
        }
        comment.update(self._input_data_iterator(input_))
        self._email_comment(comment, COMMENT_EMAIL)
        web.header('Content-Type', 'text/html')
        return self.ACK_MSG % {'return_url': input_.return_url}
    # pylint enable=C0103

    @staticmethod
    def _sanitize_field(data_, max_size=None):
        """
        Sanitize a string for use as a yaml value.
        """
        if max_size is not None:
            data = data_[:max_size]
        else:
            data = data_
        return data.replace("'", "").replace('\n', '\n  ')

    def _input_data_iterator(self, input_):
        """
        Transforms the POST input as returned by web.input() into a dictionary.
        This only keeps the keys that we are interested, truncates values to a
        maximum size and sanitizes the values.
        """
        keys = ( 'author', 'author_email', 'author_url', 'content', 'post_id')
        for key in keys:
            if hasattr(input_, key):
                max_size = MAX_SIZE
                if key == 'content':
                    max_size = MAX_SIZE_COMMENT
                value = self._sanitize_field(getattr(input_, key), max_size)
                yield (key, value)

    @staticmethod
    def _yml_from_dict(dict_):
        """
        Generates a yaml string from a dict
        """
        yaml = u""
        for item in dict_.iteritems():
            yaml += u"%s: '%s'\n" % item
        return yaml

    @staticmethod
    def _file_name(comment):
        """
        Generates a suitable file name for a comment
        """
        return comment['date_gmt'].replace(' ', '_') + '.yaml'

    def _email_comment(self, comment, email):
        """
        Send a comment by email
        """
        comment_string = self._yml_from_dict(comment)
        comment_string = comment_string.encode('UTF-8')
        comment_attachment = MIMEText(comment_string,
                                      #_subtype='x-yaml',
                                      _charset='UTF-8')
        comment_attachment.add_header('Content-Disposition', 'inline',
                                      filename=self._file_name(comment))

        message = MIMEMultipart()
        message['Subject'] = "[blogcomment] New comment from %s on %s" % (
                                                      comment['author_email'],
                                                      comment['post_id'])
        message['From'] = FROM_EMAIL
        message['To'] = email
        message.attach(MIMEText("A new comment has been posted!\n"))


        message.attach(comment_attachment)

        if not is_test():
            smtp_connection = smtplib.SMTP(**self.SMTPCONF)
            smtp_connection.sendmail(email, [email], message.as_string())
            smtp_connection.quit()

# pylint: enable=W0232

# limit the size of POST requests to 10kb
cgi.maxlen = MAX_SIZE_COMMENT
app = web.application(URLS, globals())

if (not is_test()) and __name__ == "__main__":
    app.run()
