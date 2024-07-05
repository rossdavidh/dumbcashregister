import   datetime
from     decimal   import    Decimal

from     django    import    forms
from     django.http         import    HttpResponseRedirect
from     django.views.generic.edit     import    CreateView, UpdateView, DeleteView
from     django.views.generic.list     import    ListView
from     django.views.generic.base     import    TemplateView
from     django.contrib.auth.mixins    import    LoginRequiredMixin

from     .models   import    *
from     infrastructure.models         import    FKey


class CustomerDataMixin(LoginRequiredMixin):

    def get_queryset(self, *args, **kwargs):
        request    = args[0] if args else kwargs.get("request") or self.request
        company    = self.request.user.user_profile.company
        query      = super().get_queryset(*args, **kwargs)
        return query.filter(company=company)

    def form_valid(self, form):
        #for create or update, we 'save' to get hold of the object,
        if hasattr(form, 'save') and callable(form.save):
            obj              = form.save(commit=False)
            obj.company      = self.request.user.user_profile.company
        else: #for delete, we assume we already have an object
            if self.object.company    != self.request.user.user_profile.company:
                raise ValueError("You are not authorized to delete this")
        return super().form_valid(form)


class CustomerPurchaseList(CustomerDataMixin,ListView):
    model          = CustomerPurchase
    fields         = "__all__"
    template_name  = "operations/listcustomerpurchases.html"
    paginate_by    = 100 

    def get_queryset(self, **kwargs):
       qs          = super().get_queryset(**kwargs)
       return qs.filter(lineitem__isnull=False).distinct()


class CustomerPurchaseCreate(CustomerDataMixin,CreateView):
    model          = CustomerPurchase
    fields         = "__all__"
    template_name  = "operations/newcustomerpurchase.html"


    def get_context_data(self, **kwargs):
        context    = super(CustomerPurchaseCreate, self).get_context_data(**kwargs)
        context["previouspurchases"]   = CustomerPurchase.objects.all()[0:50]
        return context

    def get_success_url(self):
        return reverse("add-lineitem", kwargs={"customer_purchase": self.object.id})


def fkeys_subtotal_and_remaining(context):
    context["fkeys"]         = FKey.objects.all()
    context["currency_symbol"]         = context["company"].currency_sym
    context["price_step_size"]         = context["company"].price_stepsize
    context["price_divisor"]           = context["company"].price_divisor
    context["price_floatformat"]       = context["company"].price_format
    lineitems      = LineItem.objects.filter(customer_purchase=context["customer_purchase"]).filter(debit=True)
    context["lineitems"]     = lineitems
    context["subtotal"]      = 0
    if len(lineitems) > 0:
        context["subtotal"]            = lineitems.aggregate(Sum("total_price"))["total_price__sum"]
    purchasepayments         = LineItem.objects.filter(customer_purchase=context["customer_purchase"]).filter(debit=False)
    context["purchasepayments"]        = purchasepayments
    context["payment_subtotal"]        = 0
    if len(purchasepayments) > 0:
        context["payment_subtotal"]          = purchasepayments.aggregate(Sum("price"))["price__sum"]
    if context["subtotal"] > context["payment_subtotal"]:
        context["remaining"] = context["subtotal"] - context["payment_subtotal"]
    else:
        context["change"]    = context["payment_subtotal"] - context["subtotal"]
    return context


class LineItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request         = kwargs.pop("request")
        super(LineItemForm, self).__init__(*args,**kwargs)
        company    = self.request.user.user_profile.company
        self.fields["price"].widget.attrs.update({"step":company.price_stepsize})

    class Meta:
        model      = LineItem
        fields     = ["price","quantity","tax_category","discount_type","payment_type","note"]
        widgets = {
            "price": forms.NumberInput(),
        }


class LineItemCreate(CustomerDataMixin,CreateView):
    model          = LineItem
    form_class     = LineItemForm
    template_name  = "operations/customerpurchase_form.html"

    def get_form_kwargs(self):
        kwargs = super(LineItemCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        purch      = CustomerPurchase.objects.get(id=self.kwargs["customer_purchase"])
        form.instance.customer_purchase          = purch
        response   = super(LineItemCreate, self).form_valid(form)
        company    = self.request.user.user_profile.company
        self.object.price    = self.object.price / company.price_divisor
        self.object.save()
        return response

    def get_context_data(self, **kwargs):
        context    = super(LineItemCreate, self).get_context_data(**kwargs)
        context["customer_purchase"]   = CustomerPurchase.objects.get(id=self.kwargs["customer_purchase"])
        if "lineitem_increment" in self.kwargs:
            li_inc = LineItem.objects.get(id=self.kwargs["lineitem_increment"])
            li_inc.quantity += 1
            li_inc.save()
        context["company"]   = self.request.user.user_profile.company
        context    = fkeys_subtotal_and_remaining(context)
        return context

    def get_success_url(self):
        return reverse("add-lineitem", kwargs={"customer_purchase": self.object.customer_purchase.id})


class LineItemUpdate(CustomerDataMixin,UpdateView):
    model          = LineItem
    form_class     = LineItemForm
    template_name  = "operations/customerpurchase_form.html"

    def get_context_data(self, **kwargs):
        context    = super(LineItemUpdate, self).get_context_data(**kwargs)
        context["updating_lineitem"]   = self.object.id
        context["customer_purchase"]   = self.object.customer_purchase
        context["company"]   = self.request.user.user_profile.company
        context    = fkeys_subtotal_and_remaining(context)
        return context

    def get_success_url(self):
        return reverse("add-lineitem", kwargs={"customer_purchase": self.object.customer_purchase.id})


class LineItemDelete(CustomerDataMixin,DeleteView):
    model          = LineItem
    template_name  = "operations/lineitem_confirm_delete.html"

    def get_success_url(self):
        return reverse("add-lineitem", kwargs={"customer_purchase": self.object.customer_purchase.id})

class DailyReport(TemplateView):
    template_name  = "operations/dailyreports.html"

    def get_context_data(self, **kwargs):
        context    = super().get_context_data(**kwargs)
        all_dates  = LineItem.objects.order_by("created_at__date").values_list("created_at__date",flat=True).distinct()
        all_dates  = [d.strftime("%Y-%m-%d") for d in all_dates]
        context["all_dates"] = all_dates
        if "the_date" not in self.kwargs:
            return context
        the_date   = datetime.datetime.strptime(self.kwargs["the_date"],"%Y-%m-%d").date()
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
