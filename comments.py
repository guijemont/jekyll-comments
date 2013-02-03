#!/usr/bin/env python
import web
import cgi
import time
import os, os.path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# config
#COMMENT_DIR = "/home/guijemont/dev/jekyll-bootstrap/_comments"
COMMENT_DIR = "_comments"
COMMENT_EMAIL = "blog@example.com"
MAX_SIZE = 1024
MAX_SIZE_COMMENT = 102400

urls = (
    '/add_comment', 'add_comment'
)

def is_test():
    webpy_env = os.environ.get('WEBPY_ENV', '')
    return webpy_env == 'test'

class add_comment:
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
    def POST(self):
        try:
            input_ = web.input()
        except ValueError:
            referer = web.ctx.env.get('HTTP_REFERER', '/')
            return self.ERROR_MSG % {'error_msg': "Input is too big, you should write less! Hit the back button and try again.",
                                     'return_url': referer}
        comment = {
            'author_ip': web.ctx.ip,
            'date_gmt': time.strftime(self.DATE_FORMAT, time.gmtime()),
            'date': time.strftime(self.DATE_FORMAT, time.localtime())
        }
        comment.update(self._input_data_iterator(input_))
        self._write_comment(comment, COMMENT_DIR)
        self._email_comment(comment, COMMENT_EMAIL)
        web.header('Content-Type', 'text/html')
        return self.ACK_MSG % {'return_url': input_.return_url}

    def _sanitize_field(self, data_, max_size=None):
        if max_size is not None:
            data = data_[:max_size]
        else:
            data = data_
        return data.replace("'", "").replace('\n', '\n  ')

    def _input_data_iterator(self, input_):
        keys = ( 'author', 'author_email', 'author_url', 'content', 'post_id')
        for key in keys:
            if hasattr(input_, key):
                max_size = MAX_SIZE
                if key == 'content':
                    max_size = MAX_SIZE_COMMENT
                yield (key, self._sanitize_field(getattr(input_, key), max_size))

    def _yml_from_dict(self, d):
        s = u""
        for item in d.iteritems():
            s += u"%s: '%s'\n" % item
        return s

    def _date_file_name(self, comment):
        return comment['date_gmt'].replace(' ', '_') + '.yaml'

    def _comment_file_name(self, comment):
        path = comment['post_id'].strip('/').replace('/', '_').replace(' ', '_')
        file_name = self._date_file_name(comment)
        return os.path.join(path, file_name)

    def _write_comment(self, comment, path):
        comment_string = self._yml_from_dict(comment)
        comment_string = comment_string.encode('UTF-8')
        filepath = self._comment_file_name(comment)
        full_file_name = os.path.join(path, filepath)
        full_path, _ = os.path.split(full_file_name)
        if not os.path.exists(full_path):
            os.mkdir(full_path)
        if not is_test():
            f = open(full_file_name, "w")
            f.write(comment_string)
            f.close()

    def _email_comment(self, comment, email):
        comment_string = self._yml_from_dict(comment)
        comment_string = comment_string.encode('UTF-8')
        comment_attachment = MIMEText(comment_string,
                                      #_subtype='x-yaml',
                                      _charset='UTF-8')
        comment_attachment.add_header('Content-Disposition', 'inline',
                                      filename=self._date_file_name(comment))

        message = MIMEMultipart()
        message['Subject'] = "[blogcomment] New comment from %s on %s" % (
                                                      comment['author_email'],
                                                      comment['post_id'])
        message['From'] = 'noreply@emont.org'
        message['To'] = email
        message.attach(MIMEText("A new comment has been posted!\n"))


        message.attach(comment_attachment)

        if not is_test():
            s = smtplib.SMTP(**self.SMTPCONF)
            s.sendmail(email, [email], message.as_string())
            s.quit()


# limit the size of POST requests to 10kb
cgi.maxlen = MAX_SIZE_COMMENT
app = web.application(urls, globals())

if (not is_test()) and __name__ == "__main__":
    app.run()
