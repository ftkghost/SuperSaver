import re
from json import loads as json_loads
from store.models import Store, StoreProperty
from supersaver.settings import make_internal_property_name


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
    name = re.sub(r"\s*--\s*", ' - ', raw_name)
    return name.replace('&amp;', '&').strip("'\"}")


def normalize_lasoo_store_address(raw_address):
    return re.sub(r"[\t\r\n]+", "", raw_address)


def add_or_update_store_in_db(store_dict, region, retailer):
    store_name = store_dict['name']
    results = retailer.stores.filter(name=store_name)
    if len(results) > 0:
        # Update existing store
        store = results[0]
    else:
        # Create new store
        store = Store()
        store.retailer = retailer
        store.region = region
        store.name = store_name
    store.display_name = store_dict["display_name"]
    store.latitude = None if 'latitude' not in store_dict else store_dict["latitude"]
    store.longitude = None if 'longitude' not in store_dict else store_dict["longitude"]
    store.tel = None if 'tel' not in store_dict else store_dict["tel"]
    store.address = None if 'address' not in store_dict else store_dict["address"]
    store.working_hours = None if 'working_hours' not in store_dict else store_dict["working_hours"]
    store.active = True
    store.save()

    lasoo_id = store_dict['lasoo_id']
    props = []
    prop = StoreProperty()
    prop.name = make_internal_property_name('lasoo_id')
    prop.value = lasoo_id
    props.append(prop)
    if 'lasoo_url' in store_dict:
        lasoo_url = store_dict['lasoo_url']
        prop = StoreProperty()
        prop.name = make_internal_property_name('lasoo_url')
        prop.value = lasoo_url
        props.append(prop)
    __update_store_props_in_db(store, props)


def __update_store_props_in_db(store, properties):
    ex_props = list(store.properties.all())
    for prop in properties:
        found = None
        for ex_prop in ex_props:
            if ex_prop.name == prop.name:
                found = ex_prop
                break
        if not found:
            # Create new props
            prop.store = store
            prop.save()
        else:
            if found.value != prop.value:
                # Update existing props
                found.value = prop.value
                found.save()
            # Remove from pending deletion list
            ex_props.remove(found)
    for p in ex_props:
        p.delete()
