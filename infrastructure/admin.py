from     django.contrib      import    admin

from     .models   import    *

admin.site.register(SoftwareVersion)
admin.site.register(Company)
admin.site.register(UserProfile)
admin.site.register(PaymentType)
admin.site.register(TaxCategory)
admin.site.register(DiscountType)
admin.site.register(FKey)
