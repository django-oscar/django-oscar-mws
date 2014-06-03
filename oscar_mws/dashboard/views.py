import logging
import oscar_mws

from django import forms
from django.http import Http404, HttpResponseRedirect
from django.views import generic
from django.contrib import messages
from django.db.models import Q, get_model
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy

from . import forms as dashboard_forms

from ..api import MWSError
from ..feeds import gateway as feeds_gw
from ..abstract_models import STATUS_DONE
from ..connection import reset_connections
from ..seller.gateway import update_marketplaces

from ..fulfillment import MwsFulfillmentError
from ..fulfillment.creator import FulfillmentOrderCreator
from ..fulfillment.gateway import (
    update_fulfillment_orders, update_inventory, submit_fulfillment_orders)

logger = logging.getLogger('oscar_mws')

Order = get_model('order', 'Order')
Product = get_model('catalogue', 'Product')
AmazonProfile = get_model("oscar_mws", "AmazonProfile")
FeedSubmission = get_model("oscar_mws", "FeedSubmission")
MerchantAccount = get_model("oscar_mws", "MerchantAccount")
FulfillmentOrder = get_model("oscar_mws", "FulfillmentOrder")
AmazonMarketplace = get_model("oscar_mws", "AmazonMarketplace")


class ProductListView(FormMixin, generic.ListView):
    template_name = 'oscar_mws/dashboard/product_list.html'
    context_object_name = 'product_list'
    form_class = dashboard_forms.MwsProductFeedForm

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
        kwargs['object_list'] = self.object_list
        kwargs[self.context_object_name] = self.object_list
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        ctx['form'] = self.get_form(form_class)
        return ctx

    def get_queryset(self):
        return Product.objects.prefetch_related('amazon_profile')

    def handle_update_stock(self, marketplace, form):
        products = self.get_selected_products(form)
        if not products:
            products = Product.objects.filter(Q(amazon_profile__isnull=False))
        try:
            update_inventory(products)
        except MWSError:
            messages.error(
                self.request, "An error occured updating available stock")
        else:
            messages.info(
                self.request, "Successfully updated available stock")

    def handle_submit_product_feed(self, marketplace, form):
        products = self.get_selected_products(form)
        if not products:
            products = Product.objects.filter(
                Q(amazon_profile=None) | Q(amazon_profile__asin=u''))
        try:
            submissions = feeds_gw.submit_product_feed(
                products=products, marketplaces=[marketplace])
        except feeds_gw.MwsFeedError:
            messages.info(
                self.request,
                ("cannot submit products to marketplaces of different "
                 "merchants within the same feed"))
            return
        except MWSError:
            messages.info(self.request, "Submitting feed to MWS failed")
            return

        submission_links = []
        for submission in submissions:
            submission_links.append(
                "<a href='{0}'>{1}</a>".format(
                    reverse(
                        'mws-dashboard:submission-detail',
                        kwargs={'submission_id': submission.submission_id}),
                    submission.submission_id))
        messages.info(
            self.request,
            "Submitted succesfully as ID(s) {0}".format(
                ', '.join(submission_links)
            ),
            extra_tags='safe',
        )

    def handle_switch_to_afn(self, marketplace, form):
        products = self.get_selected_products(form)
        if not products:
            products = Product.objects.filter(
                Q(amazon_profile=None) |
                Q(amazon_profile__marketplaces=marketplace)
            )
        if not products:
            messages.error(
                self.request, _('No products specified to switch to AFN'))
            return
        AmazonProfile.objects.filter(
            product__in=[p.id for p in products],
        ).update(
            fulfillment_by=AmazonProfile.FULFILLMENT_BY_AMAZON
        )
        try:
            submission = feeds_gw.switch_product_fulfillment(
                marketplace, products=products)
        except MWSError:
            messages.info(self.request, "Submitting feed failed")
        else:
            messages.info(
                self.request, "Submitted succesfully as ID {0}".format(
                    submission.submission_id))

    def handle_update_product_identifiers(self, marketplace, form):
        products = self.get_selected_products(form)
        if not products:
            products = Product.objects.filter(
                amazon_profile__marketplaces__isnull=False
            )
        try:
            feeds_gw.update_product_identifiers(marketplace.merchant, products)
        except MWSError as exc:
            messages.error(self.request,
                           "An error occurred retrieving product data from "
                           "Amazon: {0}".format(exc.message))
        else:
            messages.info(self.request, "Updated product ASINs")

    def form_valid(self, form):
        marketplace = form.cleaned_data.get('marketplace')
        if not marketplace:
            messages.error(
                self.request,
                _("No merchant account for Amazon selected but required.")
            )
            return self.render_to_response(self.get_context_data())
        selected = form.cleaned_data.get('submission_selection')
        if selected and hasattr(self, 'handle_{0}'.format(selected)):
            getattr(self, 'handle_{0}'.format(selected))(marketplace, form)

        return self.render_to_response(self.get_context_data())

    def get_selected_products(self, form):
        profile_ids = map(int, form.data.getlist('selected_profiles'))
        if not profile_ids:
            return Product.objects.none()
        return Product.objects.filter(amazon_profile__id__in=profile_ids)

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


class AmazonProfileCreateView(generic.CreateView):
    template_name = 'oscar_mws/dashboard/amazon_profile_create.html'
    model = AmazonProfile
    form_class = dashboard_forms.AmazonProfileCreateForm
    success_url = reverse_lazy('mws-dashboard:profile-list')

    def dispatch(self, *args, **kwargs):
        try:
            self.product = Product.objects.get(pk=kwargs.get('pk'))
        except Product.DoesNotExist:
            return HttpResponseRedirect(reverse('mws-dashboard:profile-list'))
        return super(AmazonProfileCreateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AmazonProfileCreateView, self).get_form_kwargs()
        kwargs.update(product=self.product)
        return kwargs


class AmazonProfileUpdateView(generic.UpdateView):
    template_name = 'oscar_mws/dashboard/amazon_profile_update.html'
    context_object_name = 'amazon_profile'
    model = AmazonProfile
    form_class = dashboard_forms.AmazonProfileUpdateForm
    success_url = reverse_lazy('mws-dashboard:profile-list')


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


class SubmissionUpdateView(generic.View):
    redirect_url = reverse_lazy('mws-dashboard:submission-list')

    def get(self, request, *args, **kwargs):
        submission_id = kwargs.get('submission_id')
        try:
            submission = FeedSubmission.objects.get(
                submission_id=submission_id
            )
        except FeedSubmission.DoesNotExist:
            messages.error(
                self.request,
                _("Could not find submission with ID {0}.").format(
                    submission_id
                )
            )
            return HttpResponseRedirect(self.redirect_url)

        try:
            feeds_gw.update_feed_submission(submission)
        except MWSError:
            messages.error(self.request, "Updating submission status failed")
            return HttpResponseRedirect(self.redirect_url)
        else:
            messages.info(
                self.request,
                "Updated feed submission {0}".format(submission_id))

        if submission.processing_status == STATUS_DONE:
            try:
                feeds_gw.process_submission_results(submission)
            except MWSError:
                messages.error(
                    "could not retrieve submission result for {}".format(
                        submission.submission_id))
        return HttpResponseRedirect(self.redirect_url)


class FulfillmentOrderCreateView(generic.FormView):
    model = FulfillmentOrder
    form_class = forms.Form
    default_fulfillment_region = oscar_mws.MWS_MARKETPLACE_GB

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

        try:
            order_creator = FulfillmentOrderCreator()
        except MwsFulfillmentError:
            logger.error(
                "could not create fulfillment order(s) from order {}".format(
                    order.number),
                exc_info=1,
                extra={'order_number': order.number,
                       'user': self.request.user.id})
            messages.error(
                self.request,
                "couldn't translate order {} into MWS-ready format".format(
                    order.number))
            return HttpResponseRedirect(self.get_order_url())

        submitted_orders = order_creator.create_fulfillment_order(order)
        submit_fulfillment_orders(submitted_orders)

        failed_orders = [
            fo for fo in submitted_orders if fo.status == fo.SUBMISSION_FAILED]
        if len(failed_orders) > 0:
            messages.error(
                self.request, _("Error submitting orders {} to Amazon").format(
                    ', '.join(failed_orders)))
        return HttpResponseRedirect(self.get_order_url())

    def get_order_url(self):
        return reverse(
            'dashboard:order-detail',
            kwargs={'number': self.kwargs.get('order_number')}
        )

    def get_order_list_url(self):
        return reverse("dashboard:order-list")


class FulfillmentOrderUpdateView(generic.View):

    def get(self, request, *args, **kwargs):
        order_number = kwargs.get('order_number')
        try:
            update_fulfillment_orders(
                FulfillmentOrder.objects.filter(order__number=order_number))
        except MWSError:
            messages.error(
                self.request, ("an error occured updating fulfillment orders, "
                               "please try again or report the problem."))

        return HttpResponseRedirect(
            reverse(
                'dashboard:order-detail',
                kwargs={'number': order_number}
            )
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


class MerchantListView(generic.ListView):
    model = MerchantAccount
    context_object_name = 'merchant_list'
    template_name = 'oscar_mws/dashboard/merchant_list.html'


class MerchantCreateView(generic.CreateView):
    model = MerchantAccount
    template_name = 'oscar_mws/dashboard/merchant_update.html'
    success_url = reverse_lazy('mws-dashboard:merchant-list')


class MerchantUpdateView(generic.UpdateView):
    model = MerchantAccount
    template_name = 'oscar_mws/dashboard/merchant_update.html'
    success_url = reverse_lazy('mws-dashboard:merchant-list')

    def form_valid(self, form):
        reset_connections()
        return super(MerchantUpdateView, self).form_valid(form)


class MerchantDeleteView(generic.DeleteView):
    model = MerchantAccount
    template_name = 'oscar_mws/dashboard/merchant_delete.html'
    success_url = '/dashboard/mws/merchants/'


class MarketplaceUpdateView(generic.View):

    def get(self, request, *args, **kwargs):
        seller_id = kwargs.get('seller_id')
        if not seller_id:
            messages.error(
                self.request,
                _("Seller ID required to update marketplaces"),
            )
        try:
            seller = MerchantAccount.objects.get(seller_id=seller_id)
        except MerchantAccount.DoesNotExist:
            messages.error(
                self.request,
                _("No seller with ID '{0}' configured").format(seller_id),
            )
            return HttpResponseRedirect(
                reverse_lazy('mws-dashboard:merchant-list'))

        try:
            update_marketplaces(seller)
        except MWSError:
            messages.error(
                self.request, "couldn't retrieve marketplaces from Amazon")

        return HttpResponseRedirect(
            reverse_lazy('mws-dashboard:merchant-list'))
