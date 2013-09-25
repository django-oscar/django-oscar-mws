from ..connection import get_connection


def update_marketplaces(seller_id):
    print get_connection().list_marketplace_participations()
