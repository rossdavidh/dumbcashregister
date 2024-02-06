from     django.urls         import    path

from     .         import    views

urlpatterns = [
    path("", views.CustomerPurchaseList.as_view(), name="customer-purchase-list"),
    path("create", views.CustomerPurchaseCreate.as_view(), name="customer-purchase-create"),
    path("add_lineitem/<str:customer_purchase>/<str:lineitem_increment>/", views.LineItemCreate.as_view(), name="add-lineitem"),
    path("add_lineitem/<str:customer_purchase>/", views.LineItemCreate.as_view(), name="add-lineitem"),
    path("<pk>/edit_lineitem/", views.LineItemUpdate.as_view(), name="update-lineitem"),
    path('<pk>/delete_lineitem/', views.LineItemDelete.as_view(), name="delete-lineitem"),
]
