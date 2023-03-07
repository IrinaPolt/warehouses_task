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
    all_items = Item.objects.all()
    items_list = [item for item in all_items]
    generated_warehouses = []
    for _ in range(amount):
        warehouse_item_limit = random.randrange(10, 1000000000000)
        new_warehouse = Warehouse.objects.create(general_limit=warehouse_item_limit)
        amount_item_types = random.randrange(1, len(items_list))
        storage_items = random.sample(items_list, amount_item_types)
        storage_items_amount = [0] * amount_item_types

        for i in range(amount_item_types):
            if i == amount_item_types - 1:
                storage_items_amount[i] = warehouse_item_limit - sum(storage_items_amount)
            else:
                storage_items_amount[i] = random.randint(
                    1, warehouse_item_limit - sum(storage_items_amount) - (amount_item_types - i - 1))
        
        for i in range(amount_item_types):
            ItemsForStorage.objects.create(item=storage_items[i], limit=storage_items_amount[i],
                                           rate=random.randrange(1, 10), warehouse=new_warehouse)
        generated_warehouses.append(new_warehouse)
    print('Успешно сгенерированы склады: ' + '; '.join([f'Склад №{warehouse.id}' for warehouse in generated_warehouses]))


def generate_client(amount):
    generated_clients = []
    all_items = Item.objects.all()
    items_list = [item for item in all_items]
    for _ in range(amount):
        amount_item_types = random.randrange(1, len(items_list))
        client_items = random.sample(items_list, amount_item_types)
        client = Client.objects.create()
        for item in client_items:
            CustomersItems.objects.create(item=item, amount=random.randrange(1, 1000000), client=client)
        generated_clients.append(client)
    print('Успешно сгенерированы клиенты: ' + '; '.join([f'Клиент №{client.id}' for client in generated_clients]))



def calculate_quickest_route(location_data, items): # склады, которые ближе
    final_sum = 0
    for warehouse_id, distance in location_data.items():
        for item in items:
            storage = ItemsForStorage.objects.get(warehouse=warehouse_id, item=item['item_id'])
            for item in storage:
                rate = item.rate
                print(rate)
                limit = item.limit
                print(limit)
           # rate = storage.values()['rate']
            #limit = storage.values()['limit']
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
