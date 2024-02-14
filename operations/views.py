import   datetime
from     decimal   import    Decimal

from     django    import    forms
from     django.views.generic.edit     import    CreateView, UpdateView, DeleteView
from     django.views.generic.list     import    ListView
from     django.views.generic.base     import    TemplateView

from     .models   import    *
from     infrastructure.models         import    FKey

CURRENCY_SYMBOL    = '$'
PRICE_STEP_SIZE    = '0.01'
PRICE_DIVISOR      = 100
PRICE_FLOATFORMAT  = 2

class CustomerPurchaseList(ListView):
    model          = CustomerPurchase
    fields         = '__all__'
    template_name  = 'operations/listcustomerpurchases.html'
    paginate_by    = 100 

class CustomerPurchaseCreate(CreateView):
    model          = CustomerPurchase
    fields         = '__all__'
    template_name  = 'operations/newcustomerpurchase.html'


    def get_context_data(self, **kwargs):
        context    = super(CustomerPurchaseCreate, self).get_context_data(**kwargs)
        context['previouspurchases']   = CustomerPurchase.objects.all()[0:50]
        return context

    def get_success_url(self):
        return reverse('add-lineitem', kwargs={'customer_purchase': self.object.id})


def fkeys_subtotal_and_remaining(context):
    context['fkeys']         = FKey.objects.all()
    #TODO: put this into the database somehow; user session/preferences?
    context['currency_symbol']         = CURRENCY_SYMBOL
    context['price_step_size']         = PRICE_STEP_SIZE
    context['price_divisor']           = PRICE_DIVISOR
    context['price_floatformat']       = PRICE_FLOATFORMAT
    lineitems      = LineItem.objects.filter(customer_purchase=context['customer_purchase']).filter(debit=True)
    context['lineitems']     = lineitems
    context['subtotal']      = 0
    if len(lineitems) > 0:
        context['subtotal']            = lineitems.aggregate(Sum("total_price"))['total_price__sum']
    purchasepayments         = LineItem.objects.filter(customer_purchase=context['customer_purchase']).filter(debit=False)
    context['purchasepayments']        = purchasepayments
    context['payment_subtotal']        = 0
    if len(purchasepayments) > 0:
        context['payment_subtotal']          = purchasepayments.aggregate(Sum("price"))['price__sum']
    if context['subtotal'] > context['payment_subtotal']:
        context['remaining'] = context['subtotal'] - context['payment_subtotal']
    else:
        context['change']    = context['payment_subtotal'] - context['subtotal']
    return context


class LineItemForm(forms.ModelForm):

    class Meta:
        model      = LineItem
        fields     = ['price','quantity','tax_category','discount_type','payment_type','note']
        widgets = {
            'price': forms.NumberInput(attrs={'step': PRICE_STEP_SIZE}),
        }


class LineItemCreate(CreateView):
    model          = LineItem
    form_class     = LineItemForm
    template_name  = 'operations/customerpurchase_form.html'

    def form_valid(self, form):
        purch      = CustomerPurchase.objects.get(id=self.kwargs['customer_purchase'])
        form.instance.customer_purchase          = purch
        response   =  super(LineItemCreate, self).form_valid(form)
        self.object.price    = self.object.price / PRICE_DIVISOR
        self.object.save()
        return response

    def get_context_data(self, **kwargs):
        context    = super(LineItemCreate, self).get_context_data(**kwargs)
        context['customer_purchase']   = CustomerPurchase.objects.get(id=self.kwargs['customer_purchase'])
        if 'lineitem_increment' in self.kwargs:
            li_inc = LineItem.objects.get(id=self.kwargs['lineitem_increment'])
            li_inc.quantity += 1
            li_inc.save()
        context    = fkeys_subtotal_and_remaining(context)
        return context

    def get_success_url(self):
        return reverse('add-lineitem', kwargs={'customer_purchase': self.object.customer_purchase.id})


class LineItemUpdate(UpdateView):
    model          = LineItem
    form_class     = LineItemForm
    template_name  = 'operations/customerpurchase_form.html'

    def get_context_data(self, **kwargs):
        context    = super(LineItemUpdate, self).get_context_data(**kwargs)
        context['updating_lineitem']   = self.object.id
        context['customer_purchase']   = self.object.customer_purchase
        context    = fkeys_subtotal_and_remaining(context)
        return context

    def get_success_url(self):
        return reverse('add-lineitem', kwargs={'customer_purchase': self.object.customer_purchase.id})


class LineItemDelete(DeleteView):
    model          = LineItem
    template_name  = 'operations/lineitem_confirm_delete.html'

    def get_success_url(self):
        return reverse('add-lineitem', kwargs={'customer_purchase': self.object.customer_purchase.id})

class DailyReport(TemplateView):
    template_name  = 'operations/dailyreports.html'

    def get_context_data(self, **kwargs):
        context    = super().get_context_data(**kwargs)
        all_dates  = LineItem.objects.order_by("created_at__date").values_list("created_at__date",flat=True).distinct()
        all_dates  = [d.strftime("%Y-%m-%d") for d in all_dates]
        context['all_dates'] = all_dates
        if "the_date" not in self.kwargs:
            return context
        the_date   = datetime.datetime.strptime(self.kwargs['the_date'],"%Y-%m-%d").date()
        context["taxcategories"]       = []
        context["subtotal"]  = {}
        context["salestax"]  = {}
        context["total"]     = {}
        for tc in TaxCategory.objects.all():
            context["taxcategories"].append(tc)
            context["subtotal"][tc.name]         = 0
            context["salestax"][tc.name]         = 0
            context["total"][tc.name]            = 0
            for li in LineItem.objects.filter(created_at__contains=the_date).filter(tax_category=tc):
                context["subtotal"][tc.name]    += li.subtotal
                context["salestax"][tc.name]    += li.salestax
            context["total"][tc.name]  = context["subtotal"][tc.name] + context["salestax"][tc.name]
        context["payment_types"]       = []
        context["nbr_txns"]            = {}
        context["payment_type_total"]  = {}
        for pt in PaymentType.objects.all():
            context["payment_types"].append(pt)
            context["nbr_txns"][pt.name]         = 0
            context["payment_type_total"][pt.name]         = 0
            for li in LineItem.objects.filter(created_at__contains=the_date).filter(payment_type=pt):
                context["nbr_txns"][pt.name]    += 1
                context["payment_type_total"][pt.name]    += li.price
        return context        
