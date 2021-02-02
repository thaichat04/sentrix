import os
import re
from io import StringIO

import yaml

ENV_VAR_PATTERN = re.compile(r'\${((?:(?!:-).)+):-([^}]*)}')


def read_conf(yaml_file_path):
    with open(yaml_file_path, encoding='utf8') as f:
        lines = f.readlines()

    patched_lines = StringIO()
    for line in lines:
        matches = ENV_VAR_PATTERN.findall(line)
        for match in matches:
            line = line.replace('${{{0}:-{1}}}'.format(match[0], match[1]), os.getenv(match[0], match[1]))
        patched_lines.write(line)
        patched_lines.write('\n')
    patched_lines.seek(0)
    return yaml.load(patched_lines, Loader=yaml.FullLoader)
