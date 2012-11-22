
# -*- coding: utf-8 -*-

'''SRFax (www.srfax.com) python library'''

import re
import json
import os.path
import base64
import logging

import suds


URL = 'https://www.srfax.com/SRF_UserFaxWebSrv.php?wsdl'

LOGGER = logging.getLogger(__name__)

RE_E164 = re.compile(r'^\+\d{7,15}$')
RE_NANP = re.compile(r'^\+1')


class SRFaxError(Exception):
    '''SRFax Exception'''

    def __init__(self, error_code, message, cause=None, retry=False):
        self.error_code = error_code
        self.message = message
        self.cause = cause
        self.retry = retry
        super(SRFaxError, self).__init__(error_code, message, cause, retry)
        LOGGER.exception("%s" % (self))

    def get_error_code(self):
        '''Get exception error code'''
        return self.error_code

    def get_cause(self):
        '''Get exception cause'''
        return self.cause

    def get_retry(self):
        '''Get retry option (should we retry the request?)'''
        return self.retry


class SRFax(object):
    '''SRFax class'''

    def __init__(self, access_id, access_pwd, caller_id=None,
                 sender_email=None, account_code=None, url=None):

        self.access_id = access_id
        self.access_pwd = access_pwd
        self.caller_id = caller_id
        self.sender_email = sender_email
        self.account_code = account_code
        self.url = url or URL
        self.client = suds.client.Client(self.url)

    def queue_fax(self, to_fax_number, filepath,
                  caller_id=None, sender_email=None, account_code=None):
        '''Queue fax for sending'''

        to_fax_number = SRFax.verify_fax_numbers(to_fax_number)
        fax_type = 'BROADCAST' if len(to_fax_number) > 1 else 'SINGLE'
        to_fax_number = '|'.join(to_fax_number)

        if isinstance(filepath, basestring):
            filepath = [filepath]
        if not isinstance(filepath, list):
            raise TypeError('filepath not properly defined')
        if len(filepath) > 5:
            raise Exception('More than 5 files defined in filepath')

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sCallerID': caller_id or self.caller_id,
            'sSenderEmail': sender_email or self.sender_email,
            'sFaxType': fax_type,
            'sToFaxNumber': to_fax_number,
            'sAccountCode': account_code or self.account_code or '',
        }
        SRFax.verify_parameters(params)

        for i in range(len(filepath)):
            path = filepath[i]
            params['sFileName_%d' % (i + 1)] = os.path.basename(path)
            params['sFileContent_%d' % (i + 1)] = SRFax.get_file_content(path)

        return self.process_request('Queue_Fax', params)

    def get_fax_status(self, fax_id):
        '''Get fax status'''

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sFaxDetailID': fax_id,
        }
        SRFax.verify_parameters(params)

        response = self.process_request('Get_FaxStatus', params)
        if len(response) == 1:
            response = response[0]
        return response

    def get_fax_inbox(self, period='ALL'):
        '''Get fax inbox'''

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sPeriod': period,
        }
        SRFax.verify_parameters(params)

        return self.process_request('Get_Fax_Inbox', params)

    def get_fax_outbox(self, period='ALL'):
        '''Get fax outbox'''

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sPeriod': period,
        }
        SRFax.verify_parameters(params)

        return self.process_request('Get_Fax_Outbox', params)

    def retrieve_fax(self, fax_filename, folder):
        '''Retrieve fax content in Base64 format'''

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sFaxFileName': fax_filename,
            'sDirection': folder,
        }
        SRFax.verify_parameters(params)

        response = self.process_request('Retrieve_Fax', params)
        if len(response) == 1:
            response = response[0]
        return response

    def delete_fax(self, fax_filename, folder):
        '''Delete fax files from server'''

        if isinstance(fax_filename, str):
            fax_filename = [fax_filename]
        if not isinstance(fax_filename, list):
            raise TypeError('fax_filename not properly defined')
        if len(fax_filename) > 5:
            raise Exception('More than 5 files defined in fax_filename')

        params = {
            'access_id': self.access_id,
            'access_pwd': self.access_pwd,
            'sDirection': folder,
        }
        SRFax.verify_parameters(params)

        for i in range(len(fax_filename)):
            params['sFileName_%d' % (i + 1)] = fax_filename[i]

        return self.process_request('Delete_Fax', params)

    def process_request(self, method, params):
        '''Process SRFax SOAP request'''

        method = getattr(self.client.service, method)
        try:
            response = method(**params)  # pylint: disable-msg=W0142
        except Exception as exc:
            raise SRFaxError('REQUESTFAILED', 'SOAP request failed',
                             cause=exc, retry=True)

        return SRFax.process_response(response)

    @staticmethod
    def process_response(response):
        '''Process SRFax SOAP response'''

        if not response:
            raise SRFaxError('INVALIDRESPONSE', 'Empty response', retry=True)
        if 'Status' not in response or 'Result' not in response:
            raise SRFaxError('INVALIDRESPONSE',
                             'Status and/or Result not in response: %s'
                             % (response), retry=True)

        result = response['Result']
        try:
            if isinstance(result, list):
                for i in range(len(result)):
                    if not result[i]:
                        continue
                    if isinstance(result[i], suds.sax.text.Text):
                        result[i] = str(result[i])
                    else:
                        result[i] = json.loads(json.dumps(dict(result[i])))
            elif isinstance(result, suds.sax.text.Text):
                result = str(result)
        except Exception as exc:
            raise SRFaxError('INVALIDRESPONSE',
                             'Error converting SOAP response',
                             cause=exc, retry=True)

        LOGGER.debug('Result: %s' % (result))

        if response['Status'] != 'Success':
            errmsg = result
            if (isinstance(errmsg, list) and len(errmsg) == 1
                    and 'ErrorCode' in errmsg[0]):
                errmsg = errmsg[0]['ErrorCode']
            raise SRFaxError('REQUESTFAILED', errmsg)

        if result is None:
            result = True

        return result

    @staticmethod
    def verify_parameters(params):
        '''Verify that dict values are set'''

        for key in params.keys():
            if params[key] is None:
                raise TypeError('%s not set' % (key))

    @staticmethod
    def is_e164_number(number):
        '''Simple check if number is in E.164 format'''

        if isinstance(number, str) and RE_E164.match(number):
            return True
        return False

    @staticmethod
    def is_nanp_number(number):
        '''Simple check if number is inside North American Numbering Plan'''

        if isinstance(number, str) and RE_NANP.match(number):
            return True
        return False

    @staticmethod
    def verify_fax_numbers(to_fax_number):
        '''Verify and prepare fax numbers for use at SRFax'''

        if isinstance(to_fax_number, basestring):
            to_fax_number = [to_fax_number]
        if not isinstance(to_fax_number, list):
            raise TypeError('to_fax_number not properly defined')

        for i in range(len(to_fax_number)):
            number = str(to_fax_number[i])
            if not SRFax.is_e164_number(number):
                raise TypeError('Number not in E.164 format: %s'
                                % (number))
            if SRFax.is_nanp_number(number):
                to_fax_number[i] = number[1:]
            else:
                to_fax_number[i] = '011' + number[1:]

        return to_fax_number

    @staticmethod
    def get_file_content(filepath):
        '''Read and return file content Base64 encoded'''

        if not os.path.exists(filepath):
            raise Exception('File does not exists: %s' % (filepath))
        if not os.path.isfile(filepath):
            raise Exception('Not a file: %s' % (filepath))

        content = None
        try:
            fdp = open(filepath, 'rb')
        except IOError:
            raise
        else:
            content = fdp.read()
            fdp.close()

        if not content:
            raise Exception('Error reading file or file empty: %s'
                            % (filepath))

        return base64.b64encode(content)
