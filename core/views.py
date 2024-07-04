from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from core.models import *
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404
import os
import requests
from django.db.models import Case, When, Value, IntegerField
from django.views.generic import View
import razorpay
from django.db import transaction
from datetime import datetime 
from decimal import Decimal, ROUND_HALF_UP
import re
from django.http import QueryDict
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags    
from num2words import num2words
from bs4 import BeautifulSoup
from indian_pincode_details import get_pincode_details
import indiapins
import json
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from xhtml2pdf import pisa
from io import BytesIO
from core.forms import *


def index(request):
    main_categories = Main_category.objects.filter(active_status='published')
    new_arrival = Product.objects.filter(new_arrival=True)
    deal_of_week = Product.objects.filter(deal_of_week=True)
    summer_sale = Product.objects.filter(summer_sale=True)
    product_images = ProductImages.objects.filter(product__in=deal_of_week)
    testimonials = Testimonials.objects.all()

    new_arrival_main_categories = Main_category.objects.filter(product__in=new_arrival).distinct()

    # Fetching product variants and variant types for products in summer sale
    product_variants = ProductVarient.objects.filter(product__in=summer_sale)
    product_variant_types = ProductVariantTypes.objects.filter(product_variant__product__in=summer_sale)

    halfway_index = len(main_categories) // 2

    first_half_categories = main_categories[:halfway_index]
    second_half_categories = main_categories[halfway_index:]
    
    for product in summer_sale:
        # Check if the product has variants
        product_has_variants = product.productvarient_set.exists()

        if product_has_variants:
            # Get the first variant
            first_variant = product.productvarient_set.first()
            first_variant_type = first_variant.productvarianttypes_set.first()

            product.first_variant_type_title = first_variant_type.variant_title if first_variant_type else None
            product.first_variant_type_id = first_variant_type.id if first_variant_type else None

            # Calculate default price without GST
            price_wo_gst = first_variant_type.varient_price if first_variant_type else product.price
            # Fetching GST rate
            gst_rate = first_variant_type.gst_rate if first_variant_type else product.gst_rate
            # Calculate default price including GST
            base_price = first_variant_type.varient_price if first_variant_type else product.price
            # Calculate GST amount
            gst_amount = base_price * Decimal(gst_rate.strip('%')) / 100
            # Calculate total price including GST and round off to two decimal places
            product.gst_inclusive_price = round(base_price + gst_amount, 2)
            # Include original variant price in the context
            product.variant_price = price_wo_gst
        else:
            # Use the existing price for the product if it doesn't have variants
            product.gst_inclusive_price = product.price * (1 + Decimal(product.gst_rate.strip('%')) / 100)
            product.variant_price = None
            product.first_variant_type_title = None
            product.first_variant_type_id = None

     # Iterate over products in new arrival to determine prices
    for product in new_arrival:
    # Check if the product has variants
        product_has_variants = product.productvarient_set.exists()

        if product_has_variants:
        # Get the first variant
            first_variant = product.productvarient_set.first()
            first_variant_type = first_variant.productvarianttypes_set.first()

            product.first_variant_type_title = first_variant_type.variant_title if first_variant_type else None
            product.first_variant_type_id = first_variant_type.id if first_variant_type else None

            # Calculate default price without GST
            price_wo_gst = first_variant_type.varient_price if first_variant_type else product.price
            # Fetching GST rate
            gst_rate = first_variant_type.gst_rate if first_variant_type else product.gst_rate
            # Calculate default price including GST
            base_price = first_variant_type.varient_price if first_variant_type else product.price
            # Calculate GST amount
            gst_amount = base_price * Decimal(gst_rate.strip('%')) / 100
        # Calculate total price including GST and round off to two decimal places
            product.gst_inclusive_price = round(base_price + gst_amount, 2)
        # Include original variant price in the context
            product.variant_price = price_wo_gst
        else:
        # Use the existing price for the product if it doesn't have variants
            product.gst_inclusive_price = product.price * (1 + Decimal(product.gst_rate.strip('%')) / 100)
            product.variant_price = None
            product.first_variant_type_title = None
            product.first_variant_type_id = None


    context = {
        "main_cat": main_categories,
        "first_half_categories": first_half_categories,
        "second_half_categories": second_half_categories,
        "new_arrival": new_arrival,
        "deal_of_week": deal_of_week,
        "summer_sale": summer_sale,
        "product_images": product_images,
        "product": product,
        "new_arrival_main_categories":new_arrival_main_categories,
        "product_variants": product_variants,
        "product_variant_types": product_variant_types,
        "testimonials": testimonials,
    }

    return render(request, 'core/index.html', context)


def category(request, main_title):
    main_categories = Main_category.objects.get(main_title=main_title)
    categories = Category.objects.filter(main_category=main_categories).exclude(cat_title="None")
    categories_all = Category.objects.all().exclude(cid="catbef1g41g2g4gbgda5dahbd")
    products_categories = Product.objects.filter(category__in=categories_all)
    products = Product.objects.filter(main_category=main_categories, product_status="published")
    product_images = ProductImages.objects.filter(product__in=products)

    product_variants = ProductVarient.objects.filter(product__in=products)
    variant_types = ProductVariantTypes.objects.filter(product_variant__in=product_variants)

    # Fetch product variations
    product_variations = ProductVariation.objects.filter(product__in=products)
    # Fetch product variation types
    variation_types = ProductVariationTypes.objects.filter(product_variation__in=product_variations)
    # Fetch product variation types prices
    variation_prices = {}
    for variation_type in variation_types:
        variation_prices[variation_type] = ProductVariationTypesPrices.objects.filter(product_variation_types=variation_type)
    
    materials = Product.objects.filter(main_category=main_categories).values_list('material', flat=True).distinct()

    selected_material = request.GET.get('material')
    if selected_material:
        products = products.filter(material=selected_material)

    prices = products.values_list('price', flat=True)
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    price_range = request.GET.get('price_range')
    if price_range:
        min_price, max_price = map(float, price_range.split(','))
        products = products.filter(price__range=(min_price, max_price))

    gst_rate = None  # Initialize gst_rate here

    # Fetching variant details for products
    for product in products:
        # Check if the product has variants
        product_has_variants = product.productvarient_set.exists()

        if product_has_variants:
            # Get the first variant
            first_variant = product.productvarient_set.first()
            first_variant_type = first_variant.productvarianttypes_set.first() if first_variant.productvarianttypes_set.exists() else None

            product.first_variant_type_title = first_variant_type.variant_title if first_variant_type else None
            product.first_variant_type_id = first_variant_type.id if first_variant_type else None  # Add this line
            
            # Calculate default price without GST
            price_wo_gst = first_variant_type.varient_price if first_variant_type else product.price
            # Fetching GST rate
            gst_rate = first_variant_type.gst_rate if first_variant_type else product.gst_rate
            # Calculate default price including GST
            base_price = first_variant_type.varient_price if first_variant_type else product.price
            # Calculate GST amount
            gst_amount = base_price * Decimal(gst_rate.strip('%')) / 100
            # Calculate total price including GST and round off to two decimal places
            product.gst_inclusive_price = round(base_price + gst_amount, 2)
            # Include original variant price in the context
            product.variant_price = price_wo_gst
        else:
            # Use the existing GST-inclusive price for the product
            product.gst_inclusive_price = product.price * (1 + Decimal(product.gst_rate.strip('%')) / 100)
            gst_rate = product.gst_rate
            # If the product doesn't have variants, set variant_price to None
            product.variant_price = None
            product.first_variant_type_title = None  # Add this line
            product.first_variant_type_id = None  # Add this line
            
    # Fetching variant details for products_categories
    for product in products_categories:
        # Check if the product has variants
        product_has_variants = product.productvarient_set.exists()

        if product_has_variants:
            # Get the first variant
            first_variant = product.productvarient_set.first()
            first_variant_type = first_variant.productvarianttypes_set.first() if first_variant.productvarianttypes_set.exists() else None

            product.first_variant_type_title = first_variant_type.variant_title if first_variant_type else None
            product.first_variant_type_id = first_variant_type.id if first_variant_type else None  # Add this line
            
            # Calculate default price without GST
            price_wo_gst = first_variant_type.varient_price if first_variant_type else product.price
            # Fetching GST rate
            gst_rate = first_variant_type.gst_rate if first_variant_type else product.gst_rate
            # Calculate default price including GST
            base_price = first_variant_type.varient_price if first_variant_type else product.price
            # Calculate GST amount
            gst_amount = base_price * Decimal(gst_rate.strip('%')) / 100
            # Calculate total price including GST and round off to two decimal places
            product.gst_inclusive_price = round(base_price + gst_amount, 2)
            # Include original variant price in the context
            product.variant_price = price_wo_gst
        else:
            # Use the existing GST-inclusive price for the product
            product.gst_inclusive_price = product.price * (1 + Decimal(product.gst_rate.strip('%')) / 100)
            gst_rate = product.gst_rate
            # If the product doesn't have variants, set variant_price to None
            product.variant_price = None
            product.first_variant_type_title = None  # Add this line
            product.first_variant_type_id = None  # Add this line

    context = {
        "main_categories": main_categories,
        "categories": categories,  # Keep the filtered categories
        "products": products,
        "products_categories": products_categories,
        "product_images": product_images,
        "min_price": min_price,
        "max_price": max_price,
        "product_variants": product_variants,
        "variant_types": variant_types,
        "gst_rate": gst_rate,  # Include gst_rate in the context
    }
    
    if materials:
        context["materials"] = materials

    return render(request, "core/category.html", context)



from django.http import JsonResponse

def fetch_pin_details(request):
    if request.method == 'GET':
        zipcode = request.GET.get('zipcode')
        print('Zipcode received:', zipcode)
        
        pin_details_list = indiapins.matching(zipcode)
        print('Pin details fetched:', pin_details_list)
        
        if pin_details_list:
            # Format all pin details to be sent in the response
            response_data = [
                {
                    'Name': pin_details.get('Name'),
                    'Region': pin_details.get('Region'),
                    'District': pin_details.get('District'),
                    'Division': pin_details.get('Division'),
                    'Block': pin_details.get('Block'),
                    'Circle': pin_details.get('Circle'),
                    'State': pin_details.get('State')
                }
                for pin_details in pin_details_list
            ]
            response = {
                'success': True,
                'data': response_data
            }
            print('Response:', response)  # Check if the response is correctly formatted
            return JsonResponse(response)
        else:
            return JsonResponse({'success': False, 'error': 'Pincode details not found'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})



def main_category(request):
    return render(request, "core/main_category.html")

def checkout(request):
    return render(request, "core/checkout.html")

def payment_failed_view(request):
    return render(request, "core/confirmation-failed.html")


def add_to_cart(request):
    # Ensure all required parameters are present
    required_params = ['id', 'title', 'qty', 'price', 'image', 'sku', 'price_wo_gst', 'gst_rate']
    for param in required_params:
        if param not in request.GET:
            return JsonResponse({"error": f"Missing parameter: {param}"}, status=400)
    
    product_id = request.GET.get('id')
    variant_id = request.GET.get('variant_id', '')  # Optional parameter
    variation_id = request.GET.get('variation_id', '')  # Optional parameter
    unique_key = f"{product_id}_{variant_id}_{variation_id}"  # Create a unique key

    try:
        qty = request.GET['qty']  # Ensure qty is an integer
        price = request.GET['price']  # Ensure price is a float
        price_wo_gst = request.GET['price_wo_gst']  # Ensure price_wo_gst is a float
        gst_rate = request.GET['gst_rate']  # Ensure gst_rate is a float
    except ValueError:
        return JsonResponse({"error": "Invalid numeric value"}, status=400)

    cart_product = {
        'product_id': product_id,
        'variant_id': variant_id,
        'variation_id': variation_id,
        'title': request.GET.get('title'),
        'qty': qty,
        'price': price,
        'image': request.GET.get('image'),
        'sku': request.GET.get('sku'),
        'price_wo_gst': price_wo_gst,
        'gst_rate': gst_rate,
    }

    if 'cart_data_obj' in request.session:
        cart_data = request.session['cart_data_obj']
        # Check if the product with the same unique key is already in the cart
        if unique_key in cart_data:
            return JsonResponse({"already_in_cart": True})
        
        cart_data[unique_key] = cart_product
    else:
        cart_data = {unique_key: cart_product}

    request.session['cart_data_obj'] = cart_data

    return JsonResponse({
        "data": request.session['cart_data_obj'], 
        'totalcartitems': len(request.session['cart_data_obj']), 
        "already_in_cart": False
    })



def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

        return render(request, "core/cart.html", {
            "cart_data": request.session['cart_data_obj'], 
            'totalcartitems': len(request.session['cart_data_obj']), 
            'cart_total_amount': cart_total_amount
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:main_category")



def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by("-date")
    related_main_categories = Main_category.objects.filter(product__in=products).distinct()
    product_images = ProductImages.objects.filter(product__in=products)
    
    total_products_count = Product.objects.count()
    if total_products_count == 0:
        percentage = 0
    else:
        percentage = (products.count() / total_products_count) * 100

    context = {
        "products": products,
        "query": query,
        "related_main_categories": related_main_categories,
        "percentage": percentage, 
        "product_images": product_images,
    }

    return render(request, "core/search.html", context)

def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    refresh_page = request.GET.get('refresh_page', False)

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
           cart_data = request.session['cart_data_obj']
           del request.session['cart_data_obj'][product_id]
           request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = {
        "cart_data": request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj']),
        'cart_total_amount': cart_total_amount,
        'refresh_page': refresh_page,  # Include refresh_page flag in context
    }

    rendered_html = render_to_string("core/cart.html", context)
    
    # Return JSON response with rendered HTML and refresh_page flag
    return JsonResponse({"data": rendered_html, 'totalcartitems': len(request.session['cart_data_obj']), 'refresh_page': refresh_page})      


def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']
    refresh_page = request.GET.get('refresh_page', False)
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
           cart_data = request.session['cart_data_obj']
           cart_data[str(request.GET['id'])]['qty'] = product_qty
           request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])


    context = render_to_string("core/cart.html", {"cart_data": request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj']), 'refresh_page': refresh_page}) 



def payment_failed_view(request):
    return render(request, "core/confirmation.html")

def payment_success_view(request):
    return render(request, "core/payment_confirm.html")

def about(request):
    return render(request, "core/about-us.html")

def tnc(request):
    return render(request, "core/tnc.html")

def contact(request):
    return render(request, "core/contact_us.html")

def career(request):
    return render(request, "core/career.html")

def write_to_ceo(request):
    return render(request, "core/write-to-ceo.html")

def blogs(request):
    blogs = Blogs.objects.all()
    for blog in blogs:
        # Parsing HTML and extracting text
        soup = BeautifulSoup(blog.blog_description, "html.parser")
        description_text = soup.get_text(separator='\n')
        # Splitting the text into lines and selecting the first two lines
        description_lines = description_text.split('\n')
        blog.short_description = '\n'.join(description_lines[:2])

    context = {
        "blogs": blogs,
    }

    return render(request, "core/blog.html", context)

def blog_details(request, blog_slug):
    blog_detail = Blogs.objects.get(blog_slug=blog_slug)

    context = {
        "blog_detail": blog_detail,
    }

    return render(request, "core/blog-details.html", context)

def grow_method(request):
    return render(request, "core/grow-method.html")

def payment_invoice(request):
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id = request.GET.get('razorpay_order_id')
    razorpay_signature = request.GET.get('razorpay_signature')

    # Retrieve form data from query parameters
    query_params = request.GET
    first_name = query_params.get('first_name')
    last_name = query_params.get('last_name')
    company_name = query_params.get('company_name')
    gst_number = query_params.get('gst_number')
    zipcode = query_params.get('zipcode')
    city = query_params.get('city')
    street_address = query_params.get('street_address')
    shipping_address = query_params.get('shipping_address')
    phone = query_params.get('phone')
    email = query_params.get('email')
    cart_total_amount = 0
    total_amount = 0
    price_wo_gst_total = 0
    total_gst = 0

    current_datetime = datetime.now()

    with open('maharashtra_zipcodes.json', 'r') as f:
        maharashtra_zipcodes = json.load(f)

        print('payment', maharashtra_zipcodes)

    if 'cart_data_obj' in request.session:
        # Initialize dictionaries to store CGST, SGST, and IGST amounts for each product
        cgst_amounts = {}
        sgst_amounts = {}
        igst_amounts = {}
        gst_amounts = {}
        gst_amounts_combined = {}  # Dictionary to store aggregated GST amounts

        # Calculate total amount, price without GST, and total GST
        for p_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * Decimal(item['price'])
            price_wo_gst_total += int(item['qty']) * Decimal(item.get('price_wo_gst', item['price']))
            price_wo_gst_final = int(item['qty']) * Decimal(item.get('price_wo_gst', item['price']))
            item_gst = (Decimal(item['price']) - Decimal(item.get('price_wo_gst', item['price']))) * int(
                item['qty'])  # Calculate GST for this item

            # Calculate GST rates
            if price_wo_gst_final != 0:
                gst_rates_final = (item_gst / price_wo_gst_final) * 100
            else:
                gst_rates_final = Decimal('0')

            item['gst_rates_final'] = gst_rates_final

            # Divide the GST amount by 2 to get CGST and SGST separately
            if zipcode in maharashtra_zipcodes:
                # For Maharashtra zip codes, calculate CGST and SGST separately
                igst_amount = Decimal('0')  # IGST will be 0
                gst_rates_final = gst_rates_final / Decimal(2)
            else:
                # For non-Maharashtra zip codes, IGST will be double of CGST
                igst_amount = item_gst
                gst_rates_final = gst_rates_final

            # Aggregate GST amounts based on GST rates
            if gst_rates_final in gst_amounts:
                gst_amounts[gst_rates_final] += item_gst
            else:
                gst_amounts[gst_rates_final] = item_gst

            total_gst += item_gst

        # Print CGST Amounts
        print("CGST Amounts:")
        for gst_rate, total_gst_amount in gst_amounts.items():
            cgst_amount = total_gst_amount / Decimal(2)
            print(f"CGST Amount: {cgst_amount}, GST Rate: {gst_rate}")

        # Print SGST Amounts
        print("\nSGST Amounts:")
        for gst_rate, total_gst_amount in gst_amounts.items():
            sgst_amount = total_gst_amount / Decimal(2)
            print(f"SGST Amount: {sgst_amount}, GST Rate: {gst_rate}")

        print("\nIGST Amounts:")
        for gst_rate, total_gst_amount in gst_amounts.items():
            igst_amount = total_gst_amount
            print(f"IGST Amount: {igst_amount}, GST Rate: {gst_rate}")

        print("GST Amounts:")
        print(gst_amounts)

        for gst_rate, total_gst_amount in gst_amounts.items():
            cgst_amount = total_gst_amount / Decimal(2)
            sgst_amount = total_gst_amount / Decimal(2)
            gst_amounts_combined[gst_rate] = {'cgst': cgst_amount, 'sgst': sgst_amount}

             # Check if the user is authenticated
        if request.user.is_authenticated:
            # If the user is logged in, associate the order with the logged-in user
            order = CartOrder.objects.create(
            user=request.user,  # Use the logged-in user
            price=total_amount
        )
        else:
            # If the user is not logged in, create the order without associating it with any user
            order = CartOrder.objects.create(
            price=total_amount
        )

        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

            cart_order_products = CartOrderItems.objects.create(
                order=order,
                invoice_no="order_id-" + str(order.id),
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        cart_total_amount = 0
        if 'cart_data_obj' in request.session:
            with transaction.atomic():
                for unique_key, item in request.session['cart_data_obj'].items():
                    cart_total_amount += int(item['qty']) * float(item['price'])
                    product_id = item['product_id']
                    product = Product.objects.get(pid=product_id)
                    client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
                    payment = client.order.create(
                        {'amount': int(item['qty']) * float(item['price']) * 100, 'currency': 'INR',
                         'payment_capture': 1})
                    product.razor_pay_order_id = payment['id']
                    product.save()

        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
        payment = client.order.create({'amount': cart_total_amount * 100, 'currency': 'INR', 'payment_capture': 1})
        cart_total_amount_rounded = round(cart_total_amount, 2)
        cart_total_amount_words = num2words(cart_total_amount_rounded, lang='en_IN')

        invoice_number, created = InvoiceNumber.objects.get_or_create()

        # Increment the invoice number
        invoice_number.increment()

        # Use the incremented invoice number for the current invoice
        invoice_no = str(invoice_number)

        half_total_gst_amount = total_gst / Decimal(2)

        context = {
            "payment": payment,
            "price_wo_gst_total": price_wo_gst_total,
            "total_gst": total_gst,
            "cgst_amounts": cgst_amounts,
            "sgst_amounts": sgst_amounts,
            "igst_amounts": igst_amounts,
            "zipcode": zipcode,
            "maharashtra_zipcodes": maharashtra_zipcodes,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature,
            'first_name': first_name,
            'last_name': last_name,
            'company_name': company_name,
            'gst_number': gst_number,
            'zipcode': zipcode,
            'city': city,
            'street_address': street_address,
            'phone': phone,
            'current_datetime':current_datetime,
            'email': email,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "igst_amounts": igst_amounts,
            "gst_rates_final": gst_rates_final,
            "shipping_address": shipping_address,
            "cart_total_amount_words": cart_total_amount_words,
            'invoice_no': invoice_no,
            "half_total_gst_amount": half_total_gst_amount,
            "gst_amounts": gst_amounts,
            "gst_rate": gst_rate,
            "gst_amounts_combined": gst_amounts_combined,
            'cart_data': request.session.get('cart_data_obj', {}),
            'totalcartitems': len(request.session.get('cart_data_obj', {})),
            'cart_total_amount': cart_total_amount,
            'cart_items': request.session.get('cart_data_obj', {})
        }
        subject = 'Payment Invoice'
        from_email = 'princesachdeva@nationalmarketingprojects.com'
        to_email = email
        html_message = render_to_string('core/thankyou-order.html', {'context': context})
        plain_message = strip_tags(html_message)

         # Generate PDF using xhtml2pdf
        html_template = render_to_string('core/payment_invoice.html', context)
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(html_template, dest=pdf_file)
        pdf_file.seek(0)

        # Create the email message
        email_message = EmailMultiAlternatives(subject, plain_message, from_email, [to_email])
        email_message.attach_alternative(html_message, "text/html")

        if not pisa_status.err:
            email_message.attach('invoice.pdf', pdf_file.read(), 'application/pdf')

         # Send the email
        email_message.send()

        # Render the invoice before clearing the cart data
        response = render(request, "core/payment_invoice.html", context)

        # Clear cart data after successful purchase and rendering the invoice
        if 'cart_data_obj' in request.session:
            del request.session['cart_data_obj']
            request.session.modified = True

        return response

def load_maharashtra_zipcodes():
    try:
        with open('maharashtra_zipcodes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def checkout_view(request):
    if 'cart_data_obj' not in request.session or not request.session['cart_data_obj']:
        messages.info(request, 'Please shop first before checkout')
        return redirect('/cart')
    
    cart_total_amount = 0
    total_amount = 0
    price_wo_gst_total = 0
    total_gst = 0
    user_zipcode = request.POST.get("checkout_zipcode")  # Get user's zipcode from the form

    with open('maharashtra_zipcodes.json', 'r') as f:
        maharashtra_zipcodes = json.load(f)

    # Check if user's zipcode is in Maharashtra
    if user_zipcode in maharashtra_zipcodes:
        # Maharashtra zipcode logic
        cgst_factor = Decimal('0.025')  # CGST rate for Maharashtra (2.5%)
        sgst_factor = Decimal('0.025')  # SGST rate for Maharashtra (2.5%)
        igst_factor = Decimal('0')      # IGST will be 0%
    else:
        # Non-Maharashtra zipcode logic
        cgst_factor = Decimal('0.09')   # CGST rate for other states (9%)
        sgst_factor = Decimal('0.09')   # SGST rate for other states (9%)
        igst_factor = Decimal('1')      # IGST will be 100%

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # If the user is logged in, associate the order with the logged-in user
        order = CartOrder.objects.create(
            user=request.user,  # Use the logged-in user
            price=total_amount
        )
    else:
        # If the user is not logged in, create the order without associating it with any user
        order = CartOrder.objects.create(
            price=total_amount
        )

    if 'cart_data_obj' in request.session:
        # Calculate total amount, price without GST, and total GST
        for unique_key, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])
            price_wo_gst_total += int(item['qty']) * float(item.get('price_wo_gst', item['price']))
            item_gst = (Decimal(item['price']) - Decimal(item.get('price_wo_gst', item['price']))) * int(item['qty'])  # Calculate GST for this item

            # Calculate CGST and SGST for each product based on the user's zipcode
            cgst = item_gst * cgst_factor
            sgst = item_gst * sgst_factor
            igst = item_gst * igst_factor

            total_gst += item_gst  # Add item's GST to total GST

            # Do whatever you want with CGST, SGST, and IGST here

    for unique_key, item in request.session['cart_data_obj'].items():
        cart_total_amount += int(item['qty']) * float(item['price'])

        # Retrieve the correct product ID from the item data
        product_id = item['product_id']

        # Ensure the product exists in the database
        try:
            product = Product.objects.get(pid=product_id)
        except Product.DoesNotExist:
            messages.error(request, f"Product with ID {product_id} does not exist.")
            return redirect('/cart')  # Redirect the user to the cart page

        cart_order_products = CartOrderItems.objects.create(
            order=order,
            invoice_no="order_id-" + str(order.id),
            item=item['title'],
            image=item['image'],
            qty=item['qty'],
            price=item['price'],
            total=float(item['qty']) * float(item['price'])
        )

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        with transaction.atomic():
            for unique_key, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])
                product_id = item['product_id']
                product = Product.objects.get(pid=product_id)
                client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
                amount_in_paise = int(float(item['qty']) * float(item['price']) * 100)
                payment = client.order.create({
                    'amount': amount_in_paise,
                    'currency': 'INR',
                    'payment_capture': 1
                })
                product.razor_pay_order_id = payment['id']
                product.save()

    client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
    total_amount_in_paise = int(cart_total_amount * 100)
    payment = client.order.create({
        'amount': total_amount_in_paise,
        'currency': 'INR',
        'payment_capture': 1
    })

    context = {
        "payment": payment,
        "price_wo_gst_total": price_wo_gst_total,
        "total_gst": total_gst,
        "user_zipcode": user_zipcode,
        "maharashtra_zipcodes": maharashtra_zipcodes,
    }

    return render(request, "core/checkout.html",
                  {'cart_data': request.session.get('cart_data_obj', {}),
                   'totalcartitems': len(request.session.get('cart_data_obj', {})),
                   'cart_total_amount': cart_total_amount,
                   **context})




@login_required
def dashboard(request):
    return render(request, "core/account_dashboard.html")

def faq(request):
    return render(request, "core/faq.html")

def thankyouorder(request):
    return render(request, "core/thankyou-order.html")

def shipping_policy(request):
    return render(request, "core/shipping-policy.html")

def cancellationandrefund(request):
    return render(request, "core/cancellationandrefund.html")

@login_required
def orders(request):
    orders = CartOrder.objects.filter(user=request.user).order_by("-id")
    context = {
        "orders": orders
    }
    return render(request, "core/account_orders.html", context)

def order_detail(request, id):
    order = CartOrder.objects.filter(user=request.user, id=id)
    products = CartOrderItems.objects.filter(order=order)

    context = {
        "products": products,
    }
    return render(request, "core/order-detail.html", context)

@login_required
def address(request):
    return render(request, "core/account_address.html")

def privacypolicy(request):
    privacy_policy = PrivacyPolicy.objects.first()  # Assuming you have a PrivacyPolicy instance
    context = {
        'privacy_policy_content': privacy_policy.privacy_policy_content if privacy_policy else ''
    }
    return render(request, 'core/privacy-policy.html', context)

class RobotsTxtView(View):
    def get(self, request, *args, **kwargs):
        # Specify the path to your robots.txt file
        robots_txt_path = os.path.join(settings.BASE_DIR, 'static', 'robots.txt')

        with open(robots_txt_path, 'r') as f:
            content = f.read()

        return HttpResponse(content, content_type='text/plain')
    
def product_new(request, title):
    product = Product.objects.get(title=title)
    product_variants = ProductVarient.objects.filter(product=product, status=True)
    product_variant_types = ProductVariantTypes.objects.filter(product_variant__in=product_variants)
    product_variations = ProductVariation.objects.filter(product=product, status=True)
    product_variation_types = ProductVariationTypes.objects.filter(product_variation__in=product_variations)
    related_products = Product.objects.filter(main_category=product.main_category).exclude(pid=product.pid)[:10]
    related_maincategory = product.main_category

    variation_prices = []
    for variation_type in product_variation_types:
        prices = ProductVariationTypesPrices.objects.filter(product=product, product_variation_types=variation_type)
        variation_prices.append((variation_type, prices))

    # Check if variants and variations exist
    has_variants = product_variants.exists()
    has_variations = product_variations.exists()

    # Fetching rate without GST
    price_wo_gst = product_variant_types.first().varient_price if product_variant_types.exists() else product.price

    # Fetching GST rate
    gst_rate = product_variant_types.first().gst_rate if product_variant_types.exists() else product.gst_rate

    # Calculating default price including GST
    base_price = product_variant_types.first().varient_price if product_variant_types.exists() else product.price

    # Calculate GST amount
    gst_amount = base_price * Decimal(gst_rate.strip('%')) / 100

    # Calculate total price including GST and round off to two decimal places
    total_price = round(base_price + gst_amount, 2)

    default_packaging_size = product_variant_types.first().packaging_size if product_variant_types.exists() else product.packing_size

    product_images = ProductImages.objects.filter(product=product)

    context = {
        "products": product,
        "product_variants": product_variants,
        "product_variant_types": product_variant_types,
        "product_variations": product_variations,
        "product_variation_types": product_variation_types,
        "variation_prices": variation_prices,
        "product_images": product_images,
        "default_price": total_price,
        "price_wo_gst": price_wo_gst,
        "default_packaging_size": default_packaging_size,
        "gst_rate": gst_rate,
        "has_variants": has_variants,
        "has_variations": has_variations,
        "related_products": related_products,
        "related_maincategory":  related_maincategory,
    }

    return render(request, "core/product.html", context)

def contact_us_view(request):
    if request.method == "POST":
        form = UserQueryForm(request.POST)
        if form.is_valid():
            # Extract data from the form
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            message = form.cleaned_data['message']
            
            # Send an email
            subject = f'Contact Us Form Submission from {name}'
            message_body = f'Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage:\n{message}'
            from_email = 'princesachdeva@nationalmarketingprojects.com'
            recipient_list = ['scriptforprince@gmail.com']  # Replace with actual recipient email

            send_mail(
                subject,
                message_body,
                from_email,
                recipient_list,
                fail_silently=False,
            )
            
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('contact-us')  # Replace with your desired redirect URL
    else:
        form = UserQueryForm()

    context = {
        'form' : form,
    }
    
    return render(request, 'core/contact_us.html', context)

def subscribe_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            send_mail(
                'New Newsletter Subscription',
                f'New subscription from: {email}',
                'scriptforprince@gmail.com',
                ['scriptforprince@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, 'Subscribed successfully!')
            return redirect('newsletter')
    else:
        form = NewsletterForm()

    return render(request, 'partials/base.html', {'form': form})




