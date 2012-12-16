#!/usr/bin/env python
import web
import time
import os.path

# config
#COMMENT_DIR = "/home/guijemont/dev/jekyll-bootstrap/_comments"
COMMENT_DIR = "_comments"
MAX_SIZE = 1024
MAX_SIZE_COMMENT = 1024000

urls = (
    '/', 'index',
    '/add_comment', 'add_comment'
)

class index:
    def GET(self):
        return "Hello, world!"


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
    def POST(self):
        input_ = web.input()
        comment = {
            'author_ip': web.ctx.ip,
            'date_gmt': time.strftime(self.DATE_FORMAT, time.gmtime()),
            'date': time.strftime(self.DATE_FORMAT, time.localtime())
        }
        comment.update(self._input_data_iterator(input_))
        self._write_comment(comment, COMMENT_DIR)
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
        s = ""
        for item in d.iteritems():
            s += u"%s: '%s'\n" % item
        return s

    def _comment_file_name(self, comment):
        path = comment['post_id'].strip('/').replace('/', '_').replace(' ', '_')
        file_name = comment['date_gmt'].replace(' ', '_') + '.yaml'
        return os.path.join(path, file_name)

    def _write_comment(self, comment, path):
        comment_string = self._yml_from_dict(comment)
        filepath = self._comment_file_name(comment)
        full_file_name = os.path.join(path, filepath)
        full_path, _ = os.path.split(full_file_name)
        if not os.path.exists(full_path):
            os.mkdir(full_path)
        f = open(full_file_name, "w")
        f.write(comment_string.encode("UTF-8"))
        f.close()


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
