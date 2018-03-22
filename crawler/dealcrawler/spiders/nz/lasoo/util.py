from json import loads as json_loads


def parse_lasoo_store_js(lasoo_store_js):
    # Store list json for google map looks like below:
    # [
    #     {id:13524191847234,latitude:-43.55240631,longitude:172.6368103,
    #       displayName:"All Power -- Cyclone Cycles &amp; Mowers Ltd'"}
    #     ,
    #     {id:13524191847738,latitude:-43.51478577,longitude:172.64381409,
    #       displayName:"All Power -- Edgeware Mowers &amp; Chainsaws Ltd'"}
    #     ,
    #     ...
    # ]
    lasoo_store_js = lasoo_store_js.replace("\t", "").replace("\n", "").replace("\r", "").replace('\'"', '"')
    if lasoo_store_js.find("\"id\"") > 0:
        store_list = json_loads(lasoo_store_js)
    else:
        store_json = lasoo_store_js \
            .replace('{id:', '{"id":') \
            .replace(',latitude:', ',"latitude":') \
            .replace(',longitude:', ',"longitude":') \
            .replace(',displayName:', ',"displayName":')
        store_list = json_loads(store_json)
    results = []
    for store in store_list:
        item = {}
        item['lasoo_id'] = str(store['id'])
        # Normalise field name and value
        item['display_name'] = normalize_lasoo_store_display_name(store['displayName'])
        item['name'] = item['display_name'].lower()
        item['latitude'] = store['latitude']
        item['longitude'] = store['longitude']
        results.append(item)
    return results


def normalize_lasoo_store_display_name(raw_name):
    return raw_name.replace(' -- ', ' - ').strip("'\"")


def normalize_lasoo_store_address(raw_address):
    return raw_address.replace("\t", "").replace("\r", "").replace("\n", "")
