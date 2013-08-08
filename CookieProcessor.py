import sqlite3
import cookielib
import urllib2


class CookieProcessor:
    @classmethod
    def get(cls):
        home = os.environ['HOME']
        firefox_db = home + "/.mozilla/firefox/aapkn9pp.default/cookies.sqlite"
        chrome_db = home + "/.config/google-chrome/Default/Cookies"
        firefox_sql = "select value from moz_cookies where baseDomain = 'nicovideo.jp' and name = 'user_session';"
        chrome_sql = "SELECT value FROM cookies WHERE host_key='.nicovideo.jp' AND name='user_session' LIMIT 1"

        db = firefox_db
        sql = firefox_sql

        connt = sqlite3.connect(db)
        cookie = connt.execute(sql).fetchone()[0]
        connt.close()

        print cookie

        cj = cookielib.CookieJar()
        ck = cookielib.Cookie(version=0, name="user_session", value=cookie, domain="nicovideo.jp", port=None, port_specified=False, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)

        cj.set_cookie(ck)

        return urllib2.HTTPCookieProcessor(cj)
