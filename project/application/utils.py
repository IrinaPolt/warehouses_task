import random
import string
from .models import Item, Client, Warehouse, ItemsForStorage, CustomersItems

TRANSP_RATE = 0.01

letters = string.ascii_lowercase


def generate_items(amount):
    items = []
    for _ in range(amount):
        items.append(Item(title=''.join(
            random.choice(letters) for i in range(10))))
    Item.objects.bulk_create(items)
    print('Успешно сгенерированы следующие товары: ' +
          '; '.join([item.title for item in items]))


def generate_warehouses(amount):
    items_list = [item for item in Item.objects.all()]
    gen_warehouses = []
    for _ in range(amount):
        w_item_limit = random.randrange(10, 1000000000000)
        new_warehouse = Warehouse.objects.create(
            general_limit=w_item_limit)
        amount_item_types = random.randrange(1, len(items_list))
        storage_items = random.sample(items_list, amount_item_types)
        storage_amount = [0] * amount_item_types

        for i in range(amount_item_types):
            if i == amount_item_types - 1:
                storage_amount[i] = (w_item_limit -
                                     sum(storage_amount))
            else:
                storage_amount[i] = (
                    random.randint(
                        1, w_item_limit - sum(storage_amount) -
                        (amount_item_types - i - 1)))

        for i in range(amount_item_types):
            ItemsForStorage.objects.create(
                item=storage_items[i], limit=storage_amount[i],
                rate=random.randrange(1, 10), warehouse=new_warehouse)
        gen_warehouses.append(new_warehouse)
    print('Успешно сгенерированы склады: ' + '; '.join(
        [f'Склад №{warehouse.id}' for warehouse in gen_warehouses]))


def generate_client(amount):
    generated_clients = []
    items_list = [item for item in Item.objects.all()]
    for _ in range(amount):
        amount_item_types = random.randrange(1, len(items_list))
        client_items = random.sample(items_list, amount_item_types)
        client = Client.objects.create()
        for item in client_items:
            CustomersItems.objects.create(
                item=item,
                amount=random.randrange(1, 1000000),
                client=client)
        generated_clients.append(client)
    print('Успешно сгенерированы клиенты: ' + '; '.join(
        [f'Клиент №{client.id}' for client in generated_clients]))


def min_transp_cost_route(location_data, items, flag):  # склады, которые ближе
    final_sum = 0
    message = ''
    for war_id, distance in location_data.items():
        for item in items:
            if item.amount == 0:
                continue
            else:
                try:
                    storage = ItemsForStorage.objects.get(
                        warehouse=war_id,
                        item=item.item.id)
                    rate = storage.rate
                    if item.amount <= storage.limit:
                        message += (
                            'Клиент может оставить весь оставшийся '
                            f'товар {item.item} на складе №{war_id} '
                            f'за {rate} y.e. Расстояние до склада: '
                            f'{distance} км\n')
                        final_sum += (
                            item.amount * rate + item.amount * distance * TRANSP_RATE)
                        storage.limit -= item.amount
                        item.amount = 0
                        if flag:
                            item.save()
                            storage.save()
                        break
                    else:
                        message += (
                            f'Клиент может оставить {storage.limit} '
                            f'товара {item.item} на складе №{war_id} '
                            f'за {rate} y.e.\n')
                        item.amount = item.amount - storage.limit
                        storage.limit = 0
                        final_sum += (
                            item.amount * rate + item.amount * distance * TRANSP_RATE)
                        if flag:
                            item.save()
                            storage.save()
                except ItemsForStorage.DoesNotExist:
                    continue
    for item in items:
        if item.amount != 0:
            message += (
                f'Не удалось найти склад для товара {item.item} '
                'или был превышен лимит хранения существующих складов\n')
    return final_sum, message


def min_storage_rate_route(distances, items, flag):
    message = ''
    final_sum = 0
    for item in items:
        if item.amount == 0:
            continue
        rates = {}
        for key in distances.keys():
            storage = ItemsForStorage.objects.filter(
                item=item.item,
                warehouse=key)
            rate = storage.values('rate')
            limit = storage.values('limit')
            if rate.exists() and limit != 0:
                rates[key] = (rate[0]['rate'], limit[0]['limit'])
        pref_warehouses = sorted(
            rates.items(), key=lambda item: item[1])  # (id, (rate, limit))
        for w_house in pref_warehouses:
            w_id = w_house[0]
            rate = w_house[1][0]
            limit = w_house[1][1]
            storage = ItemsForStorage.objects.get(
                item=item.item, warehouse=w_house)
            if item.amount <= limit:
                message += (
                    f'Весь оставшийся товар {item.item} '
                    f'может быть размещен на складе №{w_id} '
                    f'за минимальную ставку {rate} y.e.\n')
                final_sum += (item.amount * rate + 
                              item.amount * distances[w_id] * TRANSP_RATE)
                storage.limit = limit - item.amount
                item.amount = 0
                if flag:
                    item.save()
                    storage.save()
                break
            elif limit < item.amount:
                message += (
                    f'Товар {item.item} может быть размещен '
                    f'на складе №{w_id} '
                    f'в количестве {limit} '
                    f'за минимальную ставку {rate} y.e.\n')
                final_sum += (item.amount * rate + 
                              item.amount * distances[w_id] * TRANSP_RATE)
                item.amount = item.amount - limit
                storage.limit = 0
                if flag:
                    item.save()
                    storage.save()
                continue
    return final_sum, message


def get_routes(client_id):
    client = Client.objects.get(id=client_id)
    print(f'Клиент №{client.id}, товары: ')  # вывести клиента
    client_items_list = [
        item for item in CustomersItems.objects.filter(client=client)]
    for item in client_items_list:
        print(f'Название: {item.item.title}, '
              f'количество: {item.amount}')  # вывести товары
    warehouses = set()
    for item in client_items_list:
        queryset = ItemsForStorage.objects.filter(item=item.item)
        warehouses_ids = set(queryset.values_list('warehouse_id', flat=True))
        warehouses.update(warehouses_ids)
    distances = {}
    for warehouse in warehouses:
        distances[warehouse] = random.randrange(1, 100)
    sorted_dict = {
        k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}
    print('\nЕсть два варианта маршрутов для клиента: выбор ближайших складов '
          'для сокращения транспортных издержек, либо '
          'выбор складов с наименьшей ставкой за хранение')
    price_1, message_1 = min_transp_cost_route(
        sorted_dict, client_items_list, flag=False)
    print('\nЦена за маршрут с близлежащими складами '
          f'составит {"{:.2f}".format(price_1)}')
    print(f'Детали маршрута: \n{message_1}')
    # повторный запрос к БД необходим,
    # чтобы одна функция рутинга не влияла на вычисления другой
    price_2, message_2 = min_storage_rate_route(
        sorted_dict,
        CustomersItems.objects.filter(client=client),
        flag=False)
    print('Цена за маршрут с более низкими ставками составит '
          f'{"{:.2f}".format(price_2)}')
    print(f'Детали маршрута: \n{message_2}')
    chosen_route = random.choice([1, 2])
    print(f'Клиент выбирает маршрут №{chosen_route}')
    if chosen_route == 1:
        min_transp_cost_route(sorted_dict, client_items_list, flag=True)
        print(f'Потрачено: {"{:.2f}".format(price_1)}. Товарный баланс клиента:\n')
    else:
        min_storage_rate_route(sorted_dict,
                               CustomersItems.objects.filter(client=client),
                               flag=True)
        print(f'Потрачено: {"{:.2f}".format(price_2)}. Товарный баланс клиента:\n')
    for item in client_items_list:
        print(f'Название: {item.item.title}, '
              f'количество: {item.amount}')
