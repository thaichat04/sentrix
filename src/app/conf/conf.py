import argparse

from app.conf.yaml_conf import read_conf

parser = argparse.ArgumentParser(description='Sentrix server.')
parser.add_argument('--conf', dest='conf', action='store', default='configuration.yaml',
                    help='Path to the server configuration yaml file')
subparsers = parser.add_subparsers()

# server command
server_parser = subparsers.add_parser('server', help='Run server')

args = parser.parse_args()
conf = read_conf(args.conf)