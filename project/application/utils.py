import random
import string
from .models import Item, Client, Warehouse, ItemsForStorage, CustomersItems


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

    