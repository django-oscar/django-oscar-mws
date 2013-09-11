from django.http import Http404, HttpResponseRedirect
from django.views import generic
from django.contrib import messages
from django.db.models import Q, get_model
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy

from boto.mws.exception import InvalidParameterValue

from django import forms

from ..feeds import gateway
from .forms import MwsProductFeedForm
from ..fulfillment.creator import FulfillmentOrderCreator
from ..fulfillment.gateway import update_fulfillment_orders

Order = get_model('order', 'Order')
Product = get_model('catalogue', 'Product')
FeedSubmission = get_model("oscar_mws", "FeedSubmission")
FulfillmentOrder = get_model("oscar_mws", "FulfillmentOrder")


class ProductListView(FormMixin, generic.ListView):
    template_name = 'oscar_mws/dashboard/product_list.html'
    context_object_name = 'product_list'
    form_class = MwsProductFeedForm

    def make_object_list(self):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None \
               and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = len(self.object_list) == 0
            if is_empty:
                raise Http404(
                    _("Empty list and '%(class_name)s.allow_empty' is False.")
                    % {'class_name': self.__class__.__name__}
                )

    def get(self, request, *args, **kwargs):
        self.make_object_list()
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        kwargs[self.context_object_name] = self.object_list
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        ctx['form'] = self.get_form(form_class)
        return ctx

    def get_queryset(self):
        return Product.objects.prefetch_related('amazon_profile')

    def handle_submit_product_feed(self):
        try:
            submission = gateway.submit_product_feed(
                Product.objects.filter(
                    Q(amazon_profile=None) | Q(amazon_profile__asin=u'')
                ),
            )
        except gateway.MwsFeedError:
            messages.info(self.request, "Submitting feed failed")
        else:
            messages.info(
                self.request,
                "Submitted succesfully as ID <a href='{0}'>{1}</a>".format(
                    reverse(
                        'mws-dashboard:submission-detail',
                        kwargs={'submission_id': submission.submission_id}
                    ),
                    submission.submission_id
                ),
                extra_tags='safe',
            )

    def handle_switch_to_afn(self):
        try:
            submission = gateway.switch_product_fulfillment(
                Product.objects.all(),
            )
        except gateway.MwsFeedError:
            messages.info(self.request, "Submitting feed failed")
        else:
            messages.info(
                self.request,
                "Submitted succesfully as ID {0}".format(
                    submission.submission_id
                )
            )

    def handle_update_product_identifiers(self):
        try:
            gateway.update_product_identifiers(Product.objects.all())
        except InvalidParameterValue as exc:
            messages.error(
                self.request,
                "An error occurred retrieving product data from "
                "Amazon: {0}".format(exc.message)
            )
        else:
            messages.info(self.request, "Updated product ASINs")

    def form_valid(self, form):
        selected = form.cleaned_data.get('submission_selection')

        print 'submitting', selected
        if selected and hasattr(self, 'handle_{0}'.format(selected)):
            getattr(self, 'handle_{0}'.format(selected))()

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.make_object_list()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('mws-dashboard:product-list')


class SubmissionListView(generic.ListView):
    template_name = 'oscar_mws/dashboard/submission_list.html'
    context_object_name = 'submission_list'
    model = FeedSubmission

    def get_queryset(self):
        return self.model.objects.prefetch_related(
            'report'
        ).order_by('-date_updated')


class SubmissionDetailView(generic.DetailView):
    template_name = 'oscar_mws/dashboard/submission_detail.html'
    pk_url_kwarg = 'submission_id'
    context_object_name = 'submission'
    model = FeedSubmission

    def get_object(self):
        submission = self.model.objects.filter(
            submission_id=self.kwargs.get('submission_id')
        ).prefetch_related('report')[:1]
        if not submission:
            raise Http404
        return submission[0]


class SubmissionUpdateView(generic.RedirectView):
    permanent = False
    redirect_url = reverse_lazy('mws-dashboard:submission-list')

    def get_redirect_url(self, **kwargs):
        submission_id = self.kwargs.get('submission_id')
        try:
            gateway.update_feed_submission(submission_id)
        except gateway.MwsFeedError:
            messages.error(self.request, "Updating submission status failed")
            return self.redirect_url
        else:
            messages.info(
                self.request,
                "Updated feed submission {0}".format(submission_id)
            )
        try:
            submission = FeedSubmission.objects.get(
                submission_id=submission_id
            )
        except FeedSubmission.DoesNotExist:
            return self.redirect_url

        if submission.processing_status == '_DONE_':
            gateway.process_submission_results(submission)

        return self.redirect_url


class FulfillmentOrderCreateView(generic.FormView):
    model = FulfillmentOrder
    form_class = forms.Form

    def form_valid(self, form):
        order_number = self.kwargs.get('order_number')
        if not order_number:
            messages.error(
                self.request,
                _("No order number provided, cannot submit to MWS")
            )
            return HttpResponseRedirect(self.get_order_list_url())

        try:
            order = Order.objects.get(number=order_number)
        except Order.DoesNotExist:
            messages.error(
                self.request,
                _("Cannot find order with ID #{0}").format(order_number)
            )
            return HttpResponseRedirect(self.get_order_list_url())

        order_creator = FulfillmentOrderCreator()
        submitted_orders = order_creator.create_fulfillment_order(order)

        if not order_creator.errors:
            messages.info(
                self.request,
                _("Successfully submitted {0} orders to Amazon").format(
                    len(submitted_orders)
                )
            )
        else:
            for order_id, error in order_creator.errors.iteritems():
                messages.error(
                    self.request,
                    _("Error submitting order {0} to Amazon: {1}").format(
                        order_id,
                        error
                    )
                )
        return HttpResponseRedirect(self.get_order_url())

    def get_order_url(self):
        return reverse(
            'dashboard:order-detail',
            kwargs={'number': self.kwargs.get('order_number')}
        )

    def get_order_list_url(self):
        return reverse("dashboard:order-list")


class FulfillmentOrderUpdateView(generic.RedirectView):
    permanent = False

    def get_redirect_url(self, order_number=None):
        update_fulfillment_orders(
            FulfillmentOrder.objects.filter(order__number=order_number)
        )
        return reverse(
            'dashboard:order-detail',
            kwargs={'number': order_number}
        )


class FulfillmentOrderDetailView(generic.DetailView):
    model = FulfillmentOrder
    pk_url_kwarg = 'fulfillment_id'
    context_object_name = 'fulfillment_order'
    template_name = 'oscar_mws/dashboard/fulfillment_detail.html'

    def get_object(self):
        filters = {
            self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)
        }
        instance = self.model.objects.filter(**filters)[:1]
        if not instance:
            raise Http404
        return instance[0]
