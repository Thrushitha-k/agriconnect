from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile,State,District,SubDistrict,Village,Wishlist
import random
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash



# views.py

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import hashers
from .models import Profile
from django.shortcuts import get_object_or_404

def otp_generator():
    return  ''.join(random.choices('0123456789', k=6))


    

def create_user(request):
    if request.method == 'POST':
        # Get the data from the POST request
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        phone_number = request.POST['phone_number']
        role = request.POST['role']  # Get role from dropdown
        state = get_object_or_404(State, id=request.POST['state'])
        district = get_object_or_404(District, id=request.POST['district'])
        subdistrict = get_object_or_404(SubDistrict,id=request.POST['subdistrict'])
        village = get_object_or_404(Village, id=request.POST['village'])
        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'blog.html', {'error': 'Invalid email format!'})

        # Validate passwords match
        if password1 != password2:
            return render(request, 'index.html', {'error_message': 'Passwords do not match'})

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'index.html', {'error_message': 'Username already exists'})
        if User.objects.filter(email=email).exists():
            return render(request, 'index.html', {'error_message': 'Email already registered'})

        # Generate OTP
        otp = otp_generator()
        # Send OTP to email
        send_mail(
            'Confirm Account',
            f'Your OTP for confirming your account is: {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        # Render OTP validation page
        return render(request, 'otp_validation.html', {
            'username': username,
            'password': password1,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'state': state,
            'district': district,
            'subdistrict': subdistrict,
            'village': village,
            'phone_number': phone_number,
            'role': role,
            'otp': otp,
        })

    return render(request, 'index.html')



from django.contrib.auth import authenticate, login

def verify_otp(request):
        
    if request.method == 'POST':
       
        otp_entered = request.POST.get('otp_entered')
        otp_sent = request.POST.get('otp_sent')  # OTP sent from the create_user view

        # Verify OTP
        if otp_entered == otp_sent:
            # Create the user and profile
             # Get the data from the POST request
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            state = request.POST.get('state')
            district = request.POST.get('district')
            subdistrict = request.POST.get('subdistrict')
            village = request.POST.get('village')
            phone_number = request.POST.get('phone_number')
            role = request.POST.get('role')
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            user.save()

            profile = Profile.objects.create(
                user=user,
                state=state,
                district=district,
                subdistrict=subdistrict,
                village=village,
                phone_number=phone_number,
                role=role,
            )
            profile.save()

            # Send confirmation email
            send_mail(
                'Account Created Successfully',
                f"Hello {first_name} {last_name}, your account has been created successfully!",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            # Log the user in
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

            type_of_profile=role
            context = {
                'user': user,
                'profile': user.profile if hasattr(user, 'profile') else None
            }

           

            if type_of_profile=='seller':
                return render(request, 'seller_profile_page.html', {'context':context})
            if type_of_profile=='customer':
                return render(request, 'customer_profile_page.html', {'context':context})




        else:
            # Invalid OTP
            return render(request, 'otp_validation.html', {'email': email, 'error_message': 'Invalid OTP'})

    return redirect('index')


def send_otp_by_forgot_password(request):
        if request.method == "POST":
            flag = request.POST.get('otp_sent_for_forgot_password')
            if flag:
                
                otp_entered = request.POST.get('otp_entered')
                otp_sent = request.POST.get('otp_sent')
                email = request.POST.get('email')
                if otp_entered == otp_sent:
                    return render(request,'reset_password.html',{'email':email})
        
            else:
                email = request.POST.get('email')
                if  email and User.objects.filter(email=email).exists():
                    otp = otp_generator()
                    # Send OTP to email
                    send_mail(
                        'Confirm Account',
                        f'Your OTP for confirming your account is: {otp}',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                    return render(request,'otp_validation.html',{'otp':otp,'forgot_password_flag':True,'email':email})
                else:
                    messages.error(request, "Please enter a valid email address.")
                    return redirect('index')  # Replace 'submit_email' with the appropriate URL name
                
def change_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Check if all fields are provided
        if not email or not new_password or not confirm_password:
            return render(request, "reset_password.html", {"error": "All fields are required", "email": email})

        # Check if passwords match
        if new_password != confirm_password:
            return render(request, "reset_password.html", {"error": "Passwords do not match", "email": email})

        # Verify if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "reset_password.html", {"error": "User does not exist", "email": email})

        # Update password
        user.password = make_password(new_password)
        user.save()

        return render(request, "reset_password.html", {"success": "Password reset successfully!"})

    return render(request, "reset_password.html")
            





from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        # Get form data
        email = request.POST.get("email")  # Assuming the email is passed in the "username" field
        password = request.POST.get("password")
        role = request.POST.get("role")
        print('inside login')
        
        # Validate form data
        if not email or not password or not role:
            print('eeror in if')
            messages.error(request, "All fields are required.")
            return redirect("index")  # Replace with your login page URL name
        print('after validation')

        # Check if a user with the given email exists
        

        # Authenticate user
        
        user = authenticate(request, username=email, password=password)
        if user is None:
            print('user is none')

        if user is not None:
            # Additional role check (if roles are stored in user profile or model)
            if hasattr(user, "profile") and user.profile.role != role:
                messages.error(request, "Role does not match.")
                return redirect("index")  # Replace with your login page URL name

            # Log in the user
            
            login(request, user)
            
            if role == "customer":
                 # Display all products posted by all sellers
                seller_profiles = Profile.objects.filter(role="seller").values_list('user', flat=True)
                products = Product.objects.filter(seller__id__in=seller_profiles)
                wishlist_product_ids = Wishlist.objects.filter(customer=request.user).values_list('product_id', flat=True)
                print(list(wishlist_product_ids))
                context={'products':products,'user':user,'profile':user.profile if hasattr(user, 'profile') else None,'wishlist_product_ids': list(wishlist_product_ids)}
                return render(request, "customer_profile_page.html", context)
                
            elif role == "seller":
                user_products = Product.objects.filter(seller=request.user)
                context = {
                    'user': user,
                    'profile': user.profile if hasattr(user, 'profile') else None,
                    'products': user_products
                }
                return render(request,"seller_profile_page.html",context)  # Redirect to seller dashboard
        else:
            messages.error(request, "Invalid email or password.")
            return redirect("index")  # Replace with your login page URL name
    else:
        # Render the login page for GET requests
        return render(request, "index.html")
    

def forgot_password(request):
    return render(request,'send_otp.html')
    





def logout_view(request):
    """
    Logs out the currently authenticated user and redirects to the homepage.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    else:
        messages.info(request, "You are not logged in.")
    return render(request,'index.html')  # Replace 'index' with your homepage URL name



from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product, ProductImage

@login_required
@csrf_exempt
def add_product(request):
    if request.method == 'POST':
        # Extract product details from the POST request
        name = request.POST.get('productName')
        category = request.POST.get('productCategory')
        unit = request.POST.get('productunit')
        price_per_unit = request.POST.get('productPrice')
        quantity_in_stock = request.POST.get('productQuantity')
        description = request.POST.get('productDescription')

        # Validate required fields
        if not all([name, category, unit, price_per_unit, quantity_in_stock, description]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)
        
        try:
            price_per_unit = float(price_per_unit)
            quantity_in_stock = int(quantity_in_stock)
        except ValueError:
            return JsonResponse({'error': 'Invalid price or quantity format.'}, status=400)

        # Create a new product
        product = Product.objects.create(
            seller=request.user,  # Assuming the logged-in user is the seller
            name=name,
            description=description,
            price_per_unit=price_per_unit,
            quantity_in_stock=quantity_in_stock,
            category=category,
            unit=unit,
        )

        # Handle uploaded images
        images = request.FILES.getlist('productImages[]')  # Retrieve multiple images
        for image in images:
            ProductImage.objects.create(product=product, image=image)
    
    # Fetch products that belong to the logged-in user (the seller)
    user_products = Product.objects.filter(seller=request.user)

   

        
    user=request.user
    context = {
                'user': user,
                'profile': user.profile if hasattr(user, 'profile') else None,
                'products': user_products
            }

    return render(request, 'seller_profile_page.html',context)  # Template for product addition (if required)


def delete_product(request, product_id):
    # Get the product object and ensure it's the logged-in user's product
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    # Delete the product
    product.delete()

    # Redirect to the profile page after deletion
    return redirect('add_product')

@login_required
@csrf_exempt
def edit_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        price_per_unit = request.POST.get('price_per_unit')

        # Ensure the product belongs to the logged-in user
        product = get_object_or_404(Product, id=product_id, seller=request.user)

        # Update the product's price
        product.price_per_unit = price_per_unit
        product.save()

        # Redirect to the user's profile page
        return redirect('add_product')
    
@login_required
@csrf_exempt
def edit_profile(request):
    profile = Profile.objects.get(user=request.user)  # Get the user's profile
    if request.method == 'POST':
        # Directly access POST data
        user = request.user
        new_email = request.POST.get('email', user.email)

        user.email=new_email
        user.first_name=request.POST.get('first_name')
        user.last_name=request.POST.get('last_name')
        user.save()
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
       
        
        # Save updated profile
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('add_product')
    return render(request, 'edit_profile.html', {'profile': profile})



@login_required
@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        

        # Check if the new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        # Update the password
        user.set_password(new_password)
        user.save()

        # Update session to prevent logout
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully!')
        return redirect('add_product')
    
    return render(request, 'change_password.html')



@login_required
def wishlist_toggle(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(customer=request.user, product=product)

        # Toggle the wishlist item
        if not created:
            wishlist_item.delete()
            status = 'removed'
        else:
            status = 'added'

        # Update the context for rendering the customer profile page
        seller_profiles = Profile.objects.filter(role="seller").values_list('user', flat=True)
        products = Product.objects.filter(seller__id__in=seller_profiles)
        wishlist_product_ids = Wishlist.objects.filter(customer=request.user).values_list('product_id', flat=True)
        context = {
            'products': products,
            'user': request.user,
            'profile': request.user.profile if hasattr(request.user, 'profile') else None,
            'wishlist_product_ids': list(wishlist_product_ids),
        }

        # Render the same page with updated context
        return render(request, "customer_profile_page.html", context)

    # Fallback in case of a GET request
    return JsonResponse({'error': 'Invalid request method'}, status=400)











def get_states(request):
    states = State.objects.all().values('id', 'name')
    return JsonResponse(list(states), safe=False)

def get_districts(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)

def get_subdistricts(request):
    district_id = request.GET.get('district_id')
    subdistricts = SubDistrict.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse(list(subdistricts), safe=False)

def get_villages(request):
    subdistrict_id = request.GET.get('subdistrict_id')
    villages = Village.objects.filter(subdistrict_id=subdistrict_id).values('id', 'name')
    return JsonResponse(list(villages), safe=False)

# Create your views here.
def index(request):
    return render(request,'index.html')
def shop(request):
    return render(request,'shop.html')

def about(request):
    return render(request,'about.html')



def blog(request):
    return render(request,'blog.html')

def contact(request):
    return render(request,'contact.html')