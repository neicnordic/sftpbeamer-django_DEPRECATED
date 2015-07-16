__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '14/Jul/2015'

from omnibus.api import publish


def update_transmission_progress(transferred_bytes, total_bytes, file_name=''):
    publish(
        # the name of the channel
        'progress',
        # the `type` of the message/event, clients use this name to register event handlers
        'update',
        # payload of the event, needs to be a dict which is JSON dumpable.
        {'transferred_bytes': transferred_bytes, 'total_bytes': total_bytes, 'file_name': file_name},
        # sender id of the event, can be None.
        sender='server'
    )
