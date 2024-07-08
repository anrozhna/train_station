from django.contrib import admin

from rail.models import (
    Crew,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
    Ticket,
)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [TicketInline]


admin.site.register(Crew)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(TrainType)
admin.site.register(Train)
admin.site.register(Journey)
admin.site.register(Ticket)
