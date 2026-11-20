from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import OrderRequestForm, RegistrationForm, InspectionForm
from .models import Order, OrderItem, ServiceType, GarmentType, Material, CustomerProfile, InspectionAct

def home(request):
    services = ServiceType.objects.filter(is_active=True)[:4]
    recent_orders = Order.objects.select_related("customer").order_by("-created_at")[:3]
    return render(request, "laundry/home.html", {"services": services, "recent_orders": recent_orders})

def services(request):
    items = ServiceType.objects.filter(is_active=True)
    return render(request, "laundry/services.html", {"services": items})

def order_list(request):
    orders = Order.objects.select_related("customer").prefetch_related("items")
    if not request.user.is_authenticated:
        orders = orders.none()
    elif not request.user.is_staff:
        orders = orders.filter(customer=request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        orders = orders.filter(Q(number__icontains=query) | Q(customer__first_name__icontains=query) |
                               Q(customer__last_name__icontains=query))
    if status:
        orders = orders.filter(status=status)
    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "laundry/order_list.html", {
        "page_obj": page_obj, "query": query, "selected_status": status,
        "statuses": Order.Status.choices
    })

def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("items__stages", "items__acts"), pk=pk)
    if not request.user.is_staff and request.user != order.customer:
        messages.error(request, "У вас нет доступа к этому заказу.")
        return redirect("order_list")
    if request.method == "POST" and not request.user.is_staff:
        action = request.POST.get("action")
        latest_act = InspectionAct.objects.filter(item__order=order).order_by("-version").first()
        if action == "approve" and latest_act:
            latest_act.status = InspectionAct.Status.APPROVED
            latest_act.save(update_fields=["status"])
            order.status = Order.Status.PROCESSING
            order.total_price = latest_act.estimated_price
            order.save(update_fields=["status", "total_price"])
            messages.success(request, "Акт осмотра подтверждён. Заказ передан в обработку.")
        elif action == "clarify":
            messages.info(request, "Запрос на уточнение отправлен сотруднику.")
        return redirect("order_detail", pk=order.pk)
    latest_act = InspectionAct.objects.filter(item__order=order).order_by("-version").first()
    can_approve = bool(latest_act and latest_act.status == InspectionAct.Status.SENT)
    return render(request, "laundry/order_detail.html", {"order": order, "can_approve": can_approve})

@login_required
def staff_inspection(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Доступно только сотрудникам химчистки.")
        return redirect("profile")
    order = get_object_or_404(Order.objects.prefetch_related("items__acts"), pk=pk)
    item = order.items.first()
    if item is None:
        messages.error(request, "В заказе пока нет позиций для осмотра.")
        return redirect("order_detail", pk=order.pk)
    latest_act = item.acts.order_by("-version").first()
    if request.method == "POST":
        form = InspectionForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data["defect"].strip()
            comment = form.cleaned_data["comment"].strip()
            if comment:
                description = f"{description}. {comment}" if description else comment
            version = (latest_act.version + 1) if latest_act else 1
            if latest_act and latest_act.status in [InspectionAct.Status.DRAFT, InspectionAct.Status.SENT]:
                latest_act.status = InspectionAct.Status.SUPERSEDED
                latest_act.save(update_fields=["status"])
            InspectionAct.objects.create(item=item, version=version,
                description=description or "Дефекты не обнаружены.",
                estimated_price=form.cleaned_data["estimated_price"], status=InspectionAct.Status.SENT)
            order.total_price = form.cleaned_data["estimated_price"]
            order.status = Order.Status.WAITING
            order.save(update_fields=["total_price", "status"])
            messages.success(request, "Акт сохранён и отправлен клиенту на подтверждение.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = InspectionForm(initial={
            "defect": latest_act.description if latest_act else "",
            "estimated_price": latest_act.estimated_price if latest_act else order.total_price,
        })
    return render(request, "laundry/staff_inspection.html", {"order": order, "item": item, "form": form})

@login_required
def create_order(request):
    if request.method == "POST":
        form = OrderRequestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            service, garment, material = data["service"], data["garment_type"], data["material"]
            price = (service.base_tariff * material.coefficient * garment.default_complexity *
                     Decimal(data["urgency"])).quantize(Decimal("0.01"))
            number = "PR-" + timezone.now().strftime("%y%m%d%H%M%S")
            order = Order.objects.create(number=number, customer=request.user, total_price=price)
            OrderItem.objects.create(order=order, garment_type=garment, service=service,
                material=material, description=data["description"],
                urgency_coefficient=Decimal(data["urgency"]), item_price=price)
            messages.success(request, f"Заявка {order.number} успешно создана.")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderRequestForm()
    return render(request, "laundry/order_form.html", {"form": form})

@login_required
def profile(request):
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")[:10]
    profile_data = getattr(request.user, "laundry_profile", None)
    return render(request, "laundry/profile.html", {"orders": orders, "profile_data": profile_data})

def about(request):
    return render(request, "laundry/about.html")

def search(request):
    query = request.GET.get("q", "").strip()
    results = Order.objects.filter(Q(number__icontains=query) | Q(customer__first_name__icontains=query) |
                                   Q(customer__last_name__icontains=query)) if query else Order.objects.none()
    if not request.user.is_staff:
        results = results.filter(customer=request.user) if request.user.is_authenticated else Order.objects.none()
    return render(request, "laundry/search.html", {"query": query, "results": results[:50]})

def search_json(request):
    query = request.GET.get("q", "").strip()
    items = ServiceType.objects.filter(is_active=True)
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return JsonResponse({"results": [
        {"id": item.pk, "name": item.name, "description": item.description,
         "price": str(item.base_tariff)} for item in items[:20]
    ]})

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect("profile")
    else:
        form = RegistrationForm()
    return render(request, "laundry/register.html", {"form": form})
