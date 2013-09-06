from django.http import Http404
from django.db.models import Q, get_model
from django.contrib import messages
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, RedirectView

from boto.mws.exception import InvalidParameterValue

from .. import feeds
from .forms import MwsProductFeedForm

Product = get_model('catalogue', 'Product')
FeedSubmission = get_model("oscar_mws", "FeedSubmission")


class ProductListView(FormMixin, ListView):
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
            if (self.get_paginate_by(self.object_list) is not None
                and hasattr(self.object_list, 'exists')):
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
            submission = feeds.submit_product_feed(
                Product.objects.filter(
                    Q(amazon_profile=None) | Q(amazon_profile__asin=u'')
                ),
            )
        except feeds.MwsFeedError:
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
            submission = feeds.switch_product_fulfillment(
                Product.objects.all(),
            )
        except feeds.MwsFeedError:
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
            feeds.update_product_identifiers(Product.objects.all())
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


class SubmissionListView(ListView):
    template_name = 'oscar_mws/dashboard/submission_list.html'
    context_object_name = 'submission_list'
    model = FeedSubmission

    def get_queryset(self):
        return self.model.objects.prefetch_related(
            'report'
        ).order_by('-date_updated')


class SubmissionDetailView(DetailView):
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


class SubmissionUpdateView(RedirectView):
    permanent = False
    redirect_url = reverse_lazy('mws-dashboard:submission-list')

    def get_redirect_url(self, **kwargs):
        submission_id = self.kwargs.get('submission_id')
        try:
            feeds.update_feed_submission(submission_id)
        except feeds.MwsFeedError:
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
            feeds.process_submission_results(submission)

        return self.redirect_url
