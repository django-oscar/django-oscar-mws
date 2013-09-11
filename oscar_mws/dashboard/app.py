from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.views.decorators import staff_member_required

from . import views


class OscarMwsDashboardApplication(Application):
    name = 'mws-dashboard'

    product_list_view = views.ProductListView

    submission_list_view = views.SubmissionListView
    submission_detail_view = views.SubmissionDetailView
    submission_update_view = views.SubmissionUpdateView

    fulfillment_order_create_view = views.FulfillmentOrderCreateView
    fulfillment_order_update_view = views.FulfillmentOrderUpdateView

    fulfillment_order_detail_view = views.FulfillmentOrderDetailView

    def get_urls(self):
        urlpatterns = patterns(
            '',
            url(
                r'^products/$',
                self.product_list_view.as_view(),
                name='product-list'
            ),
            url(
                r'^submissions/$',
                self.submission_list_view.as_view(),
                name='submission-list'
            ),
            url(
                r'^submission/(?P<submission_id>[\w-]+)/$',
                self.submission_detail_view.as_view(),
                name='submission-detail'
            ),
            url(
                r'^submission/update/(?P<submission_id>[\w-]+)/$',
                self.submission_update_view.as_view(),
                name='submission-update'
            ),
            url(
                r'^fulfillment/create/(?P<order_number>[\w-]+)/$',
                self.fulfillment_order_create_view.as_view(),
                name='fulfillment-create'
            ),
            url(
                r'^fulfillment/update/(?P<order_number>[\w-]+)/$',
                self.fulfillment_order_update_view.as_view(),
                name='fulfillment-update'
            ),
            url(
                r'^fulfillment/(?P<fulfillment_id>[\w-]+)/$',
                self.fulfillment_order_detail_view.as_view(),
                name='fulfillment-detail'
            ),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = OscarMwsDashboardApplication()
