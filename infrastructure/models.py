from     decimal   import    Decimal

from     django.db import    models
from     django.dispatch     import receiver
from     django.core.validators        import    MaxValueValidator, MinValueValidator
from     django.contrib.auth.models    import    User
from     django.db.models.signals      import    post_save

DECIMAL_100        = Decimal("100")
DECIMAL_2          = Decimal("2")

class SoftwareVersion(models.Model):
    version_id     = models.DateField()
    installed_datetime       = models.DateTimeField()
    replaced_datetime        = models.DateTimeField(null=True,blank=True,unique=True)
    #NOTE: to find current version, use SoftwareVersion.objects.filter(replaced_datetime__isnull=True)[0]

    class Meta:
        ordering   = ["-installed_datetime"]

    def __str__(self):
        rep        = str(self.version_id)
        rep       += ", installed: "
        rep       += str(self.installed_datetime.date())
        return rep


class Company(models.Model):
    company_name   = models.CharField(max_length=200,unique=True)
    currency_sym   = models.CharField(max_length=4,default="$")
    price_stepsize = models.CharField(max_length=20,default="0.01")
    price_divisor  = models.DecimalField(decimal_places=10,
                                         max_digits=20,
                                         validators=[
                                             MinValueValidator(1.0)
                                         ],
                                         default=DECIMAL_100)
    price_format   = models.DecimalField(decimal_places=10,
                                         max_digits=20,
                                         validators=[
                                             MinValueValidator(0.0)
                                         ],
                                         default=DECIMAL_2,
                                         verbose_name="Price format (how many decimal places to display in prices)")

    def __str__(self):
        return self.company_name

    @classmethod
    def get_default_pk(cls):
        test, created = cls.objects.get_or_create(
            company_name="test",
        )
        return test.pk


class CRModel(models.Model):
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    company        = models.ForeignKey(Company,on_delete=models.CASCADE,default=Company.get_default_pk)

    def software_version_when_created(self):
        return SoftwareVersion.objects.filter(installed_datetime__lte=self.created_at)[0].version_id

    def software_version_when_updated(self):
        return SoftwareVersion.objects.filter(installed_datetime__lte=self.updated_at)[0].version_id


class UserProfile(CRModel):
    user = models.OneToOneField(User,on_delete=models.CASCADE, related_name='user_profile')

    def __str__(self):
        return str(self.user)+" - " + self.company.company_name

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
            UserProfile.objects.create(user=instance).save()


class PaymentType(CRModel):
    name = models.CharField(max_length=200,unique=True)
    #TODO: remove calculate_change, after verifying it is not needed
    calculate_change         = models.BooleanField(default=False,verbose_name="For this payment method, calculate change returned to customer")
    order          = models.IntegerField()

    class Meta:
        ordering   = ["order"]

    def __str__(self):
        return self.name


class TaxCategory(CRModel):
    name = models.CharField(max_length=200,unique=True)
    tax_rate       = models.DecimalField(decimal_places=10,
                                         max_digits=10,
                                         validators=[
                                             MaxValueValidator(1.0),
                                             MinValueValidator(0.0)
                                         ],)
    order          = models.IntegerField()

    class Meta:
        ordering   = ["order"]
 
    def __str__(self):
        return self.name


class DiscountType(CRModel):
    name = models.CharField(max_length=200,unique=True)
    discount_rate  = models.DecimalField(decimal_places=10,
                                         max_digits=10,
                                         validators=[
                                             MaxValueValidator(1.0),
                                             MinValueValidator(0.0)
                                         ],)
    begin_date     = models.DateField(null=True,blank=True)
    end_date       = models.DateField(null=True,blank=True)

    def __str__(self):
        return self.name


class FKey(CRModel):
    KEY_CHOICES    = {
                      "F1": "F1",
                      "F2": "F2",
                      "F3": "F3",
                      "F4": "F4",
                      "F5": "F5",
                      "F6": "F6",
                      "F7": "F7",
                      "F8": "F8",
                      "F9": "F9",
                      "F10": "F10",
                      "F11": "F11",
                      "F12": "F12",
                      "ESC": "ESC",
                      "/":"/",
                      "*":"*",
                      "-":"-",
                      "+":"+",
                      ".":".",
                      "PageDown":"PageDown",
                      "PageUp":"PageUp",
                      }
    KEY_TYPES      = {
                      "PaymentType": "PaymentType",
                      "TaxCategory": "TaxCategory",
                      "Discount": "Discount",
                      }
    key  = models.CharField(max_length=8,choices=KEY_CHOICES,unique=True)
    payment_type   = models.ForeignKey(PaymentType,on_delete=models.CASCADE,null=True,blank=True)
    tax_category   = models.ForeignKey(TaxCategory,on_delete=models.CASCADE,null=True,blank=True)
    discount_type  = models.ForeignKey(DiscountType,on_delete=models.CASCADE,null=True,blank=True)
    key_type       = models.CharField(max_length=20,choices=KEY_TYPES,null=True,blank=True,editable=False)
    display_order  = models.IntegerField(default=0,unique=False)

    class Meta:
        ordering   = ["display_order"]

    def __str__(self):
        rep        = str(self.key)+" "
        if self.payment_type:
            rep   += str(self.payment_type)
        elif self.tax_category:
            rep   += str(self.tax_category)
        elif self.discount_type:
            rep   += str(self.discount_type)
        return rep

    def save(self, *args, **kwargs):
        if self.payment_type and self.tax_category or \
           self.tax_category and self.discount_type or \
           self.payment_type and self.discount_type:
               raise ValueError("FKey can be only one of payment type, tax category, or discount type")
        elif self.payment_type:
            self.key_type    = "PaymentType"
        elif self.tax_category:
            self.key_type    = "TaxCategory"
        elif self.discount_type:
            self.key_type    = "DiscountType"
        else:
            raise ValueError("FKey must be either a payment type, tax category, or discount type")
        super().save(*args, **kwargs)  # Call the "real" save() method.


