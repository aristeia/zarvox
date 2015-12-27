'''Python SpinPapi client

  File: SpinPapiClient.py
  Author Tom Worster
  Copyright (c) 2012 Spinitron, LLC. All rights reserved.
  Redistribution and use in source and binary forms, with or without modification, are permitted
  	provided that the following conditions are met:
   * Redistributions of source code must retain the above copyright notice, this list of conditions
   		and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright notice, this list of
   		conditions and the following disclaimer in the documentation and/or other materials provided
   		with the distribution.
   * Neither the name of the Spinitron, LLC. nor the names of its contributors may be used to endorse
   		or promote products derived from this software without specific prior written permission.
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
  IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
  FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
  OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  '''

import hmac, hashlib, base64, sys, binascii 
from urllib.parse import quote
from time import gmtime, strftime
from operator import itemgetter

class SpinPapiClient:
  '''A SpinPapi client class.

    {@see http://spinitron.com/user-guide/pdf/SpinPapi-v2.pdf}
    NOTE: all SpinPapi client applications must cache result data. This
    class does not provide caching.
    '''

  def __init__(self, userid, secret, station=''):
    '''Client constructor.

      :param string userid: Authentication user ID issued by Spinitron
      :param string secret: Authentication secret issued by Spinitron
      :param string station: Station ID
      '''

    self.params = {}
    self.params['papiversion'] = '2'
    self.host = 'spinitron.com'
    self.url = '/public/spinpapi.php'
    self.params['papiuser'] = userid
    self.secret = secret
    self.params['station'] = station

  def query(self, params):
    '''Perform an uncached SpinPapi query.

      :param dict params: SpinPapi query parameters. At least method
        must be present in the dict.

      :return string: A complete signed query URL.
      '''

    # Add requested params to object default params
    all_params = self.params
    for key, val in params.items():
      all_params[key] = val

    # Add current GMT timestamp to params
    all_params['timestamp'] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())

    # Sort params alphabetically by dict key
    all_params = sorted(all_params.items(), key=itemgetter(0))

    # Build the urlencoded query in a list and join it with '&' chars
    the_query = []
    for key, val in all_params:
      the_query.append(quote(key) + '=' + quote(val))
    the_query = '&'.join(the_query)

    # Construct the query's HMAC signature.
    signature = bytes(self.host + '\n' + self.url + '\n' + the_query, 'utf-8')
    signature = hmac.new(self.secret, signature, hashlib.sha256)
    signature = signature.digest()
    signature = base64.b64encode(signature)
    signature = quote(signature, '')

    return ('http://' + self.host + self.url
        + '?' + the_query + '&signature=' + signature)
