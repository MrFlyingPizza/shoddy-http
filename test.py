import unittest

from shoddyhttp import HttpRequest, HttpResponse, http_request_from_raw, HttpStatusCode, HttpStatusMessage


class HttpStatusTest(unittest.TestCase):
    def test_all_codes_and_messages_are_matched(self):
        codes_names = [c.name for c in HttpStatusCode]
        messages_names = [c.name for c in HttpStatusMessage]
        self.assertListEqual(codes_names, messages_names)


class HttpRequestObjectTest(unittest.TestCase):
    raw = ("GET / HTTP/1.1\n"
           "Host: 127.0.0.1\n"
           "Connection: keep-alive\n"
           "sec-ch-ua: \"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"\n"
           "sec-ch-ua-mobile: ?0\n"
           "sec-ch-ua-platform: \"Windows\"\n"
           "Upgrade-Insecure-Requests: 1\n"
           "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
           "like Gecko) Chrome/107.0.0.0 Safari/537.36\n"
           "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
           "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\n"
           "Sec-Fetch-Site: none\n"
           "Sec-Fetch-Mode: navigate\n"
           "Sec-Fetch-User: ?1\n"
           "Sec-Fetch-Dest: document\n"
           "Accept-Encoding: gzip, deflate, br\n"
           "Accept-Language: en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7\n"
           "dnt: 1\n"
           "\n")

    def test_construction(self):
        headers = {
            "Host": "127.0.0.1",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/107.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "dnt": "1"
        }

        expected_string = self.raw

        self.assertEqual(expected_string, HttpRequest(url="/", headers=headers).to_raw())

    def test_construction_from_raw(self):
        self.assertEqual(self.raw, http_request_from_raw(self.raw).to_raw())


class HttpResponseObjectTest(unittest.TestCase):
    raw = ("HTTP/1.1 200 OK\n"
           "Date: Sun, 04 Dec 2022 07:23:10 GMT\n"
           "Content-Type: text/html\n"
           "Content-Length: 2335\n"
           "Connection: keep-alive\n"
           "Content-Encoding: gzip\n"
           "Last-Modified: Fri, 08 Apr 2022 16:54:52 GMT\n"
           "Accept-Ranges: bytes\n"
           "ETag: \"0d6835d694bd81:0\"\n"
           "Vary: Accept-Encoding\n"
           "Server: Microsoft-IIS/10.0\n"
           "X-Powered-By: ASP.NET\n"
           "SN: EC2AMAZ-BSL60ON\n"
           "\n")

    def test_construction(self):
        headers = {
            "Date": "Sun, 04 Dec 2022 07:23:10 GMT",
            "Content-Type": "text/html",
            "Content-Length": "2335",
            "Connection": "keep-alive",
            "Content-Encoding": "gzip",
            "Last-Modified": "Fri, 08 Apr 2022 16:54:52 GMT",
            "Accept-Ranges": "bytes",
            "ETag": "\"0d6835d694bd81:0\"",
            "Vary": "Accept-Encoding",
            "Server": "Microsoft-IIS/10.0",
            "X-Powered-By": "ASP.NET",
            "SN": "EC2AMAZ-BSL60ON"
        }

        expected_string = self.raw

        self.assertEqual(expected_string, HttpResponse(headers=headers).to_raw())


if __name__ == "__main__":
    unittest.main()
