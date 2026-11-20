from django.conf import settings
from django.db import models
from django.db.models import Q

class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="laundry_profile", verbose_name="Пользователь")
    phone = models.CharField("Телефон", max_length=20, unique=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    created_at = models.DateTimeField("Дата регистрации", auto_now_add=True)
    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"
        ordering = ["user__last_name", "user__first_name"]
    def __str__(self): return f"{self.user} ({self.phone})"

class ServiceType(models.Model):
    name = models.CharField("Наименование услуги", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    base_tariff = models.DecimalField("Базовый тариф", max_digits=8, decimal_places=2)
    is_active = models.BooleanField("Активна", default=True)
    class Meta:
        verbose_name = "Вид услуги"
        verbose_name_plural = "Виды услуг"
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=Q(base_tariff__gte=0), name="service_tariff_nonnegative")]
    def __str__(self): return self.name

class Material(models.Model):
    name = models.CharField("Материал", max_length=80, unique=True)
    coefficient = models.DecimalField("Коэффициент материала", max_digits=5, decimal_places=2)
    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=Q(coefficient__gt=0), name="material_coef_positive")]
    def __str__(self): return self.name

class GarmentType(models.Model):
    name = models.CharField("Тип вещи", max_length=100, unique=True)
    category = models.CharField("Категория", max_length=50)
    default_complexity = models.DecimalField("Коэффициент сложности", max_digits=5, decimal_places=2, default=1)
    class Meta:
        verbose_name = "Тип вещи"
        verbose_name_plural = "Типы вещей"
        ordering = ["category", "name"]
        constraints = [models.CheckConstraint(condition=Q(default_complexity__gt=0), name="garment_complexity_positive")]
    def __str__(self): return self.name

class Order(models.Model):
    class Status(models.TextChoices):
        NEW="new", "Новый"; INSPECTION="inspection", "Осмотр"; WAITING="waiting", "Ожидает согласия"
        PROCESSING="processing", "В обработке"; QUALITY="quality", "Контроль качества"
        READY="ready", "Готов"; ISSUED="issued", "Выдан"; CANCELLED="cancelled", "Отменён"
    number = models.CharField("Номер заказа", max_length=20, unique=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="laundry_orders", verbose_name="Клиент")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    due_date = models.DateField("Плановая дата готовности", null=True, blank=True)
    total_price = models.DecimalField("Итоговая стоимость", max_digits=10, decimal_places=2, default=0)
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=Q(total_price__gte=0), name="order_total_nonnegative")]
    def __str__(self): return self.number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    garment_type = models.ForeignKey(GarmentType, on_delete=models.PROTECT, related_name="order_items", verbose_name="Тип вещи")
    service = models.ForeignKey(ServiceType, on_delete=models.PROTECT, related_name="order_items", verbose_name="Услуга")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="order_items", verbose_name="Материал")
    description = models.CharField("Описание вещи", max_length=255, blank=True)
    urgency_coefficient = models.DecimalField("Коэффициент срочности", max_digits=5, decimal_places=2, default=1)
    item_price = models.DecimalField("Стоимость вещи", max_digits=10, decimal_places=2)
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        ordering = ["order_id", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(urgency_coefficient__gt=0), name="item_urgency_positive"),
            models.CheckConstraint(condition=Q(item_price__gte=0), name="item_price_nonnegative")]
    def __str__(self): return f"{self.order.number}: {self.garment_type}"

class InspectionAct(models.Model):
    class Status(models.TextChoices):
        DRAFT="draft", "Черновик"; SENT="sent", "Отправлен клиенту"
        APPROVED="approved", "Подтверждён"; REJECTED="rejected", "Отклонён"; SUPERSEDED="superseded", "Заменён новой версией"
    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="acts", verbose_name="Позиция заказа")
    version = models.PositiveSmallIntegerField("Версия акта")
    description = models.TextField("Результат осмотра")
    estimated_price = models.DecimalField("Оценочная стоимость", max_digits=10, decimal_places=2)
    status = models.CharField("Статус", max_length=15, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    approved_at = models.DateTimeField("Дата согласия", null=True, blank=True)
    class Meta:
        verbose_name = "Акт осмотра"
        verbose_name_plural = "Акты осмотра"
        ordering = ["item_id", "-version"]
        constraints = [models.UniqueConstraint(fields=["item", "version"], name="unique_act_version"),
            models.CheckConstraint(condition=Q(version__gte=1), name="act_version_positive")]
    def __str__(self): return f"Акт {self.item_id}, версия {self.version}"

class Defect(models.Model):
    name = models.CharField("Дефект", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    acts = models.ManyToManyField(InspectionAct, through="ActDefect", related_name="defects", verbose_name="Акты осмотра")
    class Meta:
        verbose_name = "Вид дефекта"
        verbose_name_plural = "Виды дефектов"
        ordering = ["name"]
    def __str__(self): return self.name

class ActDefect(models.Model):
    act = models.ForeignKey(InspectionAct, on_delete=models.CASCADE, related_name="act_defects")
    defect = models.ForeignKey(Defect, on_delete=models.PROTECT, related_name="act_defects")
    note = models.CharField("Примечание", max_length=255, blank=True)
    location = models.CharField("Расположение", max_length=100, blank=True)
    class Meta:
        verbose_name = "Дефект в акте"
        verbose_name_plural = "Дефекты в актах"
        constraints = [models.UniqueConstraint(fields=["act", "defect", "location"], name="unique_act_defect_location")]
    def __str__(self): return f"{self.defect} — акт {self.act_id}"

class ProcessingStage(models.Model):
    class Status(models.TextChoices):
        WAITING="waiting", "Ожидает"; IN_PROGRESS="in_progress", "Выполняется"; DONE="done", "Завершён"
    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="stages", verbose_name="Позиция заказа")
    name = models.CharField("Этап обработки", max_length=100)
    sequence = models.PositiveSmallIntegerField("Порядок этапа")
    status = models.CharField("Статус", max_length=15, choices=Status.choices, default=Status.WAITING)
    started_at = models.DateTimeField("Начало", null=True, blank=True)
    finished_at = models.DateTimeField("Окончание", null=True, blank=True)
    class Meta:
        verbose_name = "Этап обработки"
        verbose_name_plural = "Этапы обработки"
        ordering = ["item_id", "sequence"]
        constraints = [models.UniqueConstraint(fields=["item", "sequence"], name="unique_item_stage")]
    def __str__(self): return f"{self.item_id}: {self.name}"

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING="pending", "Ожидает"; PAID="paid", "Оплачен"; REFUNDED="refunded", "Возвращён"
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments", verbose_name="Заказ")
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    method = models.CharField("Способ оплаты", max_length=30)
    status = models.CharField("Статус", max_length=15, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField("Дата оплаты", null=True, blank=True)
    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-paid_at", "-id"]
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive")]
    def __str__(self): return f"{self.order.number}: {self.amount}"
