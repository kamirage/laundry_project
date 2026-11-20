"""
Пять запросов для приложения laundry.
Запуск: python manage.py shell < orm_queries_demo.py
"""
from django.db.models import Count, Avg, Sum
from laundry.models import Order, OrderItem, InspectionAct, Defect

# 1. Фильтрация: заказы, ожидающие согласия акта
q1 = Order.objects.filter(status="waiting").order_by("created_at")
print("Q1 ORM:", q1)
print("Q1 SQL:", q1.query)
print("Q1 RESULT:", list(q1.values_list("number", "status")[:10]))

# 2. Сортировка: самые дорогие позиции
q2 = OrderItem.objects.select_related("order", "garment_type").order_by("-item_price")
print("Q2 ORM:", q2)
print("Q2 SQL:", q2.query)
print("Q2 RESULT:", list(q2.values_list("order__number", "garment_type__name", "item_price")[:10]))

# 3. Агрегация: количество заказов, средний и общий чек
q3 = Order.objects.aggregate(
    orders_count=Count("id"), average_check=Avg("total_price"), revenue=Sum("total_price")
)
print("Q3 ORM: Order.objects.aggregate(Count, Avg, Sum)")
print("Q3 SQL: агрегирующий SQL формируется ORM; см. queryset.query для исходного queryset")
print("Q3 RESULT:", q3)

# 4. Выборка по связи 1:N с select_related
q4 = OrderItem.objects.select_related("order", "service", "material").filter(order__status="processing")
print("Q4 ORM:", q4)
print("Q4 SQL:", q4.query)
print("Q4 RESULT:", list(q4.values_list("order__number", "service__name", "material__name")[:10]))

# 5. M:N через явную связующую модель, prefetch_related
q5 = InspectionAct.objects.prefetch_related("defects").filter(status="approved")
print("Q5 ORM:", q5)
print("Q5 SQL:", q5.query)
for act in q5[:10]:
    print("Q5 RESULT:", act.id, act.item.order.number, list(act.defects.values_list("name", flat=True)))
