import random
import string
from .models import Item, Client, Warehouse, ItemsForStorage, CustomersItems

TRANSPORTATION_RATE = 0.01

letters = string.ascii_lowercase


def generate_items(amount):
    items = []
    for i in range(amount):
        items.append(Item(title=''.join(random.choice(letters) for i in range(10))))
    Item.objects.bulk_create(items)
    print('Успешно сгенерированы следующие товары: ' + '; '.join([item.title for item in items]))


def generate_warehouses(amount):
    items = Item.objects.all()
    warehouses = []
    for i in range(amount):
        warehouse_limit = random.randrange(10, 1000000000000)
        new_warehouse = Warehouse.objects.create(general_limit=warehouse_limit)
        amount_item_types = random.randrange(1, len(items))
        storage_items = []
        while sum(item.limit for item in storage_items) < warehouse_limit:
            num_items = random.randint(1, warehouse_limit - sum(item.limit for item in storage_items))
            items_list = [ItemsForStorage(item=random.choice(items), limit=random.randint(1, num_items),
                                          rate=random.randrange(0, 10), warehouse=new_warehouse) for _ in range(amount_item_types)]
            storage_items.extend(items_list)
        ItemsForStorage.objects.bulk_create(storage_items)
        new_warehouse.save()
        warehouses.append(new_warehouse)
    print('Успешно сгенерированы склады: ' + '; '.join([f'Склад №{warehouse.id}' for warehouse in warehouses]))


def generate_client(amount):
    clients = []
    items = Item.objects.all()
    for i in range(amount):
        amount_item_types = random.randrange(0, len(items))
        client = Client.objects.create()
        for k in range(amount_item_types):
            CustomersItems.objects.create(item=random.choice(items), amount=random.randrange(0, 1000000), client=client)
        client.save()
        clients.append(client)
    print('Успешно сгенерированы клиенты: ' + '; '.join([f'Клиент №{client.id}' for client in clients]))



def calculate_quickest_route(location_data, items): # склады, которые ближе
    final_sum = 0
    for warehouse_id, distance in location_data.items():
        for item in items:
            storage = ItemsForStorage.objects.filter(warehouse=warehouse_id, item=item['item_id'])
            rate = storage.values()['rate']
            limit = storage.values()['limit']
            if limit - item['amount'] >= 0:
                final_sum += item['amount'] * rate + distance * TRANSPORTATION_RATE
                break
            else:
                final_sum += (item['amount'] - limit) * rate + distance * TRANSPORTATION_RATE
                item['amount'] == item['amount'] - limit
    print(final_sum)


def get_routes(client_id):
    client = Client.objects.get(id=client_id)
    #print(client) # вывести клиента
    client_items = list(CustomersItems.objects.filter(client=client).values())
    #print(*client_items) # вывести его товары
    warehouses = set()
    for item in client_items:
        queryset = ItemsForStorage.objects.filter(item=item['item_id']).values() # здесь нужно отсортировать по rate и limit ?
        warehouses_ids = set(queryset.values_list('warehouse_id', flat=True))
        warehouses.update(warehouses_ids)
    distances = {}
    for warehouse in warehouses:
        distances[warehouse] = random.randrange(1, 100)
    sorted_dict = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}
    calculate_quickest_route(sorted_dict, client_items)
