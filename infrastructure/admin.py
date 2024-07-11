from     django.contrib      import    admin

from     .models   import    *

admin.site.register(SoftwareVersion)
admin.site.register(UserProfile)

class PaymentTypeAdmin(admin.ModelAdmin):
    model          = PaymentType
    def get_queryset(self, request):
        if request.user.is_superuser:
            return PaymentType.objects.all()
        try:
            return PaymentType.objects.filter(company=request.user.user_profile.company)
        except:
            return PaymentType.objects.none()
admin.site.register(PaymentType,PaymentTypeAdmin)


class TaxCategoryAdmin(admin.ModelAdmin):
    model          = TaxCategory
    def get_queryset(self, request):
        if request.user.is_superuser:
            return TaxCategory.objects.all()
        try:
            return TaxCategory.objects.filter(company=request.user.user_profile.company)
        except:
            return TaxCategory.objects.none()
admin.site.register(TaxCategory,TaxCategoryAdmin)


class DiscountTypeAdmin(admin.ModelAdmin):
    model          = DiscountType
    def get_queryset(self, request):
        if request.user.is_superuser:
            return DiscountType.objects.all()
        try:
            return DiscountType.objects.filter(company=request.user.user_profile.company)
        except:
            return DiscountType.objects.none()
admin.site.register(DiscountType,DiscountTypeAdmin)


class FKeyAdmin(admin.ModelAdmin):
    model          = FKey
    def get_queryset(self, request):
        if request.user.is_superuser:
            return FKey.objects.all()
        try:
            return FKey.objects.filter(company=request.user.user_profile.company)
        except:
            return FKey.objects.none()
admin.site.register(FKey,FKeyAdmin)


class CompanyAdmin(admin.ModelAdmin):
    model          = Company
    search_fields  = ("company_name", "currency_sym")

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Company.objects.all()
        try:
            return Company.objects.filter(id=request.user.user_profile.company.id)
        except:
            return Company.objects.none()
admin.site.register(Company, CompanyAdmin)

