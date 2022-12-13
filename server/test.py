import logging

FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)
d = {'clientip': '192.168.0.1', 'user': 'fbloggs'}
logger = logging.getLogger('socket_client')

def main():
    logger.warning('Protocol problem: %s', extra=d)
    pass

if __name__ == '__main__':
    main()