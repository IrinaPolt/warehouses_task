from django.db import models


class Item(models.Model):
    title = models.CharField(
        max_length=250,
        verbose_name='Наименование товара'
    )

    def __str__(self):
        return self.title


class Warehouse(models.Model):
    storage = models.ManyToManyField(
        Item,
        through='ItemsForStorage',
        verbose_name = 'Товары на хранение',
        )
    general_limit = models.PositiveIntegerField(
        verbose_name='Общий лимит товара для данного склада'
    )


class ItemsForStorage(models.Model):
    """Вспомогательная модель для создания склада: позволяет добавить тип принимаемого товара,
    лимит и тарифы"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name='Товар')
    limit = models.PositiveIntegerField(
        verbose_name='Лимит данного товара для данного склада'
    )
    rate = models.PositiveSmallIntegerField(
        verbose_name='Тариф за хранение данного товара на данном складе'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name='Склад'
    )


class Client(models.Model):
    items = models.ManyToManyField(
        Item,
        through='CustomersItems',
        verbose_name='Товары у клиента'
    )


class CustomersItems(models.Model):
    item = models.ForeignKey(
        Item,
        verbose_name='Товар',
        on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        verbose_name='Количество товара у данного клиента'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE)
