try:
    from ConfigParser import ConfigParser
except ImportError:
    import configparser as ConfigParser # py3k support
import requests, time, json
from sys import stderr


headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'whatapi [isaaczafuta]'
    }

class LoginException(Exception):
    pass


class RequestException(Exception):
    pass


class WhatAPI:
    def __init__(self, config_file=None, username=None, password=None, cookies=None):
        self.request_time = 0
        self.session = requests.Session()
        self.session.headers = headers
        self.session.mount('https://',requests.adapters.HTTPAdapter(max_retries=3))
        self.authkey = None
        self.passkey = None
        if config_file:
            config = ConfigParser()
            config.read(config_file)
            self.username = config.get('login', 'username')
            self.password = config.get('login', 'password')
        else:
            self.username = username
            self.password = password
        if cookies:
            self.session.cookies = cookies
            try:
                self._auth()
            except RequestException:
                self._login()
        else:
            self._login()

    def _auth(self):
        '''Gets auth key from server'''
        accountinfo = self.request("index")
        self.authkey = accountinfo["response"]["authkey"]
        self.passkey = accountinfo["response"]["passkey"]



    def _login(self):
        '''Logs in user'''
        loginpage = 'https://ssl.what.cd/login.php'
        data = {'username': self.username,
                'password': self.password,
                'keeplogged': 1,
                'login': 'Login'
        }
        r = self.session.post(loginpage, data=data, allow_redirects=False)
        if r.status_code != 302:
            raise LoginException
        self._auth()

    def get_torrent(self, torrent_id):
        '''Downloads the torrent at torrent_id using the authkey and passkey'''
        torrentpage = 'https://ssl.what.cd/torrents.php'
        params = {'action': 'download', 'id': torrent_id}
        if self.authkey:
            params['authkey'] = self.authkey
            params['torrent_pass'] = self.passkey
        time_diff = 2-time.clock()+self.request_time
        if time_diff > 0:
            time.sleep(time_diff)
        r = self.session.get(torrentpage, params=params, allow_redirects=False)
        self.request_time = time.clock()
        if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
            return r.content
        return None

    def logout(self):
        '''Logs out user'''
        logoutpage = 'https://ssl.what.cd/logout.php'
        params = {'auth': self.authkey}
        self.session.get(logoutpage, params=params, allow_redirects=False)

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        ajaxpage = 'https://ssl.what.cd/ajax.php'
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)
        json_response = {"status": None}
        try:
            time_diff = 2-time.clock()+self.request_time
            if time_diff > 0:
                time.sleep(time_diff)
            r = self.session.get(url=ajaxpage, 
                params=params, 
                allow_redirects=False, 
                timeout=(0.67,9.5))
            self.request_time = time.clock()
            r.raise_for_status()
            json_response = r.json()
            if action != "similar_artists" and json_response["status"] != "success":
                print("Response status is not successful, it is "+json_response["status"], file=stderr)
                raise RequestException()
            return json_response
        except requests.exceptions.ConnectionError as e:
            print("Cannot resolve domain")
            print(e, file=stderr)
        except requests.exceptions.ConnectTimeout as e:
            print("Couldn't connect to server; trying again")
            print(e, file=stderr)
        except requests.exceptions.HTTPError as e:
            print("HTTPError with server, ",e.message)
            print(e, file=stderr)
        except ValueError as e:
            print("Valueerror decoding json")
            print(e, file=stderr)
        except Exception as e:
            print("Some other issue with whatcd request", e)
            print(e, file=stderr)
            print(json_response)
        raise RequestException