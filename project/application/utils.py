import random
import string
from .models import Item, Client, Warehouse, ItemsForStorage, CustomersItems

TRANSPORTATION_RATE = 0.01

letters = string.ascii_lowercase


def generate_items(amount):
    items = []
    for _ in range(amount):
        items.append(Item(title=''.join(random.choice(letters) for i in range(10))))
    Item.objects.bulk_create(items)
    print('Успешно сгенерированы следующие товары: ' + '; '.join([item.title for item in items]))


def generate_warehouses(amount):
    items_list = [item for item in Item.objects.all()]
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
    items_list = [item for item in Item.objects.all()]
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
            if item.amount == 0:
                continue
            else:
                try:
                    storage = ItemsForStorage.objects.get(warehouse=warehouse_id, item=item.item.id)
                    rate = storage.rate
                    if item.amount <= storage.limit:
                        print(f'Клиент может оставить весь оставшийся товар {item.item} на складе №{warehouse_id}')
                        final_sum += item.amount * rate + distance * TRANSPORTATION_RATE
                        storage.limit -= item.amount
                        item.amount = 0
                        break
                    else:
                        print(f'Клиент может оставить {storage.limit} товара {item.item} на складе №{warehouse_id}')
                        item.amount = item.amount - storage.limit
                        storage.limit = 0
                        final_sum += item.amount * rate + distance * TRANSPORTATION_RATE
                except ItemsForStorage.DoesNotExist:
                    continue
    for item in items:
        if item.amount != 0:
            print(f'Не удалось найти склад для товара {item.item} или был превышен лимит хранения существующих складов')
    print(f'Итоговая сумма для пути с наиболее близкими складами: {final_sum}')


def calculate_lowest_rate_route(distances, items): # склады с более дешевой ставкой
    visited_warehouses = {}
    final_sum = 0
    for item in items:
        if len(visited_warehouses) != 0:
            for warehouse in visited_warehouses.keys():
                try:
                    storage = ItemsForStorage.objects.get(item=item.item, warehouse=warehouse)
                    limit = visited_warehouses[warehouse]
                    if 0 < item.amount <= limit:
                        print(f'Весь оставшийся товар {item.item} может быть размещен на складе №{warehouse}')
                        final_sum += item.amount * storage.rate
                        visited_warehouses[warehouse] -= item.amount 
                        item.amount = 0
                    else:
                        print(f'Товар {item.item} может быть размещен на складе №{warehouse} в количестве {limit}')
                        final_sum += item.amount * storage.rate
                        item.amount -= limit
                        visited_warehouses[warehouse] = 0
                except ItemsForStorage.DoesNotExist:
                    continue
        rates = {}

        # нужно прерывать цикл, если лимит склада или количество товара равны нулю. где и как?

        for key in distances.keys():
            storage = ItemsForStorage.objects.filter(item=item.item, warehouse=key)
            rate = storage.values('rate')
            limit = storage.values('limit')
            if rate.exists():
                rates[key] = (rate[0]['rate'], limit[0]['limit'])
            else:
                print(f'{item.item} не может быть размещен на складе №{key}')
        preferrable_warehouse = sorted(rates.items(), key=lambda item: item[1])[0] # (id, (rate, limit))
        storage = ItemsForStorage.objects.get(item=item.item, warehouse=preferrable_warehouse[0])
        if item.amount <= preferrable_warehouse[1][1]:
            print(f'Весь оставшийся товар {item.item} может быть размещен на складе №{preferrable_warehouse[0]}')
            final_sum += item.amount * preferrable_warehouse[1][0] + distances[preferrable_warehouse[0]] * TRANSPORTATION_RATE
            storage.limit = preferrable_warehouse[1][1] - item.amount
            item.amount = 0
            visited_warehouses[preferrable_warehouse[0]] = storage.limit
        elif preferrable_warehouse[1][1] < item.amount:
            print(f'Товар {item.item} может быть размещен на складе №{preferrable_warehouse[0]} в количестве {preferrable_warehouse[1][1]}')
            item.amount = item.amount - preferrable_warehouse[1][1]
            storage.limit = 0
            final_sum += item.amount * preferrable_warehouse[1][0] + distances[preferrable_warehouse[0]] * TRANSPORTATION_RATE
    print(f'Итоговая сумма для пути со складами с более низкой ставкой: {final_sum}')


def get_routes(client_id):
    client = Client.objects.get(id=client_id)
    #print(client) # вывести клиента
    client_items_list = [item for item in CustomersItems.objects.filter(client=client)]
    #print(client_items_list) # вывести его товары
    warehouses = set()
    for item in client_items_list:
        queryset = ItemsForStorage.objects.filter(item=item.item)
        warehouses_ids = set(queryset.values_list('warehouse_id', flat=True))
        warehouses.update(warehouses_ids)
    distances = {}
    for warehouse in warehouses:
        distances[warehouse] = random.randrange(1, 100)
    sorted_dict = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}
    calculate_quickest_route(sorted_dict, client_items_list)
    calculate_lowest_rate_route(sorted_dict, CustomersItems.objects.filter(client=client)) # повторный запрос к БД необходим, чтобы одна функция рутинга не влияла на вычисления другой
