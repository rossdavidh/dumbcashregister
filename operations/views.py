from     decimal   import    Decimal

from     django    import    forms
from     django.views.generic.edit     import    CreateView, UpdateView, DeleteView
from     django.views.generic.list     import    ListView

from     .models   import    *
from     infrastructure.models         import    FKey


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
            'price': forms.NumberInput(attrs={'step': 0.01}),
        }


class LineItemCreate(CreateView):
    model          = LineItem
    form_class     = LineItemForm
    template_name  = 'operations/customerpurchase_form.html'

    def form_valid(self, form):
        purch      = CustomerPurchase.objects.get(id=self.kwargs['customer_purchase'])
        form.instance.customer_purchase          = purch
        return super(LineItemCreate, self).form_valid(form)

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

