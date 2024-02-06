import   time
import   datetime
from     django.db import    models
from     django.db.models    import    Sum
from     django.urls         import    reverse

from     infrastructure.models         import    *



def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
    return utc + offset


class CustomerPurchase(CRModel):
    #represents a customer, at the cash register at a particular day and time,
    #making a purchase of one or more items.
    class Meta:
        ordering   = ["-created_at"]

    def __str__(self):
        return datetime.datetime.strftime(utc2local(self.created_at),"%Y-%m-%d %H:%M:%S")

    def total_payments(self):
        purch_pmts = PurchasePayment.objects.filter(customer_purchase=self)
        if len(purch_pmts) > 0:
            return purch_pmts.aggregate(Sum("amount"))
        else:
            return 0

    def sum_total(self):
        lineitems  = LineItem.objects.filter(customer_purchase=self)
        if len(lineitems) > 0:
            return lineitems.aggregate(Sum("total_price"))
        else:
            return 0


def get_default_tax_category():
    return TaxCategory.objects.all()[0].id

class LineItem(CRModel):
    customer_purchase        = models.ForeignKey(CustomerPurchase,on_delete=models.CASCADE)
    price          = models.DecimalField(decimal_places=10,
                                         max_digits=20,
                                         validators=[
                                             MinValueValidator(0.0)
                                         ],)
    quantity       = models.IntegerField(default=1,
                                         validators=[
                                             MinValueValidator(1)
                                         ],)
    tax_category   = models.ForeignKey(TaxCategory,on_delete=models.PROTECT,null=True,blank=True)
    discount_type  = models.ForeignKey(DiscountType,on_delete=models.PROTECT,null=True,blank=True)
    payment_type   = models.ForeignKey(PaymentType,on_delete=models.PROTECT,null=True,blank=True)
    total_price    = models.DecimalField(null=True,blank=True,
                                         decimal_places=10,
                                         max_digits=20,
                                         validators=[
                                             MinValueValidator(0.0)
                                         ],
                                         editable=False)
    debit          = models.BooleanField(default=True,editable=False)
    note           = models.CharField(max_length=200,blank=True)

    class Meta:
        ordering   = ["customer_purchase","-created_at"]

    def __str__(self):
        return str(self.customer_purchase) + ", $" + str(round(self.price,2))

    def save(self, *args, **kwargs):
        if self.payment_type:
            self.debit       = False
            if self.tax_category or self.discount_type:
                raise ValueError("Lineitems with PaymentType cannot have TaxCategory or DiscountType.")
        else:
            if not self.tax_category:
                #Default tax category is set by "order" field of TaxCategory
                #TODO: check if this line is ever actually needed
                self.tax_category      = TaxCategory.objects.all()[0]
            self.total_price = self.price * self.quantity * (1+self.tax_category.tax_rate) 
            if self.discount_type:
                self.total_price       = self.total_price * (1-self.discount_type.discount_rate)
        super().save(*args, **kwargs)  # Call the "real" save() method.
