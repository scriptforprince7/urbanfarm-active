from django.urls import include, path
from core.views import *

app_name = "core"

urlpatterns = [
    path("", index, name="index"),
    path("shop-category/", main_category, name="main_category"),
    path("category/<main_title>/", category, name="category"),
    path("product/<title>/", product_new, name="product_new"),
    path("add-to-cart/", add_to_cart, name="add-to-cart"),
    path("search/", search_view, name="search"),
    path("delete-from-cart/", delete_item_from_cart, name="delete-from-cart"),
    path("update-cart/", update_cart, name="update-cart"),
    path("checkout/", checkout_view, name="checkout"),
    path("about-us/", about, name="about-us"),
    path("contact-us/", contact, name="contact-us"),
    path('contact-us/', contact_us_view, name='contact_us'),
    path("career", career, name="career"),
    path("faq", faq, name="faq"),
    path("shipping-policy/", shipping_policy, name="shipping_policy"),
    path("termsandconditions/", tnc, name="tnc"),
    path("blog/", blogs, name="blogs"),
    path('newsletter/', subscribe_newsletter, name='subscribe_newsletter'),
    path("grow-method/", grow_method, name="grow_method"),
    path('fetch-pin-details/', fetch_pin_details, name='fetch_pin_details'),
    path("blog/<blog_slug>/", blog_details, name="blog_details"),
    path("privacy-policy/", privacypolicy, name="privacypolicy"),
    path("cancellationandrefund/", cancellationandrefund, name="cancellationandrefund"),
    path("cart/", cart_view, name="cart_view"),
    path("payment-failed/", payment_failed_view, name="payment_failed_view"),
    path("thankyouorder/", thankyouorder, name="thankyouorder"),
    path("payment-success/", payment_success_view, name="payment_success_view"),
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/myorders", orders, name="orders"),
    path("dashboard/myaddress", address, name="address"),
    path("dashboard/myorders/<int:id>", order_detail, name="order_detail"),
    path("payment-invoice/", payment_invoice, name="payment_invoice"),
]
