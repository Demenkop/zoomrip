import re


auth_re = re.compile(r'config.auth = "(.*)";')
ts_re = re.compile(r"config.ts = '(.*)';")
url_re = re.compile(r"http.*://.*\.zoom\.us/j/(\d*)(\?pwd=(.*)|)")
