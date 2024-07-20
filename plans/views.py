from django.shortcuts import render, get_object_or_404, redirect
from .forms import CustomSignupForm
from django.urls import reverse_lazy
from django.views import generic
from .models import FitnessPlan, Customer
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
import stripe
from django.http import HttpResponse

stripe.api_key = 'sk_test_51NLvHoK8kJfVRpKYxZySCLsVgMnGS1dy2aC8KOlqWT9fQ3LuzOYDSoVmcFlfJ2mMoSXeaI7O5WkMzwHjmou83MhF0084CrLLfn'

@user_passes_test(lambda u: u.is_superuser) #only people who are superusers can access the following URL.
def updateaccounts(request) :
    customers = Customer.objects.all() #so we'll go get all of our customers in customers.
    for customer in customers :
        subscription = stripe.Subscription.retrieve(customer.stripe_subscription_id) #so bel retrieve togna njibo ga3 les infos(id) ta3 subscriptions
        if subscription.status != "active" : #status dayrtha stripe, So, once we have the subscription we're going to check and see if it's valid
            customer.membership = False
        else :
            customer.membership = True
        customer.cancel_at_period_end = subscription.cancel_at_period_end #This allows the customer object to have the same cancellation behavior as the subscription object, By setting cancel_at_period_end to True, the subscription or customer will be set to cancel at the end of the current billing period
        customer.save() #saves the changes
        return HttpResponse('completed')

def home(request):
    plans = FitnessPlan.objects
    return render(request, 'plans/home.html', {'plans':plans})

def plan(request,pk):
    plan = get_object_or_404(FitnessPlan, pk=pk) #  If the object does not exist, it raises a 404 error
    if plan.premium : #if a user click on Get Premium on the home page.
        if request.user.is_authenticated : #if he logged in
            try :
                if request.user.customer.membership : 
                    return render(request, 'plans/plan.html', {'plan':plan})
            except Customer.DoesNotExist :
                return redirect('join')
        return redirect('join') # join is a url name
    else:
        return render(request, 'plans/plan.html', {'plan':plan})

def join(request):
    return render(request, 'plans/join.html')

@login_required
def checkout(request):

    try :
        if request.user.customer.membership : 
            return redirect('settings')
    except Customer.DoesNotExist :
        pass
    coupons = {'halloween':31, 'welcome':10}
    if request.method == 'POST' : #hadi m3a talya ki dekhel les infos ta3 la carte bancaire ta3k
        stripe_customer = stripe.Customer.create(email=request.user.email, source=request.POST['stripeToken']) #stripe.Customer.create It creates a new customer object, email howa email ta3 customer, source représente where it is that this customer's coming from using the key, is a dictionary contains the data submitted (the key) that represents the payment details such as credit card information.
        plan = 'price_1NMI6aK8kJfVRpKYyEvETngx' #jebna had ID mn site stripe Products -> Name dkhelna fl Nick Fitness Premium-> 3nd Pricing copiena API ID ta3 month
        if request.POST['plan'] == 'yearly' :
            plan = 'price_1NMIDBK8kJfVRpKYW69F6Vki' #kima lfoganiya chawala copina ID ta3 yearly
        if request.POST['coupon'] in coupons :
            percentage = coupons[request.POST['coupon'].lower()]
            try:
                coupon = stripe.Coupon.create(duration='once', id=request.POST['coupon'].lower(), percent_off=percentage) #This code attempts to create a coupon in Stripe, The value 'once' indicates that the coupon can only be used once by a customer, id tmetel coupon li ydekhleh user, percent_off ymetel tekhfidat 
            except:
                pass #Any errors encountered during the coupon creation are caught and ignored
            subscription = stripe.Subscription.create(customer=stripe_customer.id, items=[{'plan': plan}],coupon=request.POST['coupon'].lower())
        else :
            subscription = stripe.Subscription.create(customer=stripe_customer.id, items=[{'plan': plan}]) #stripe.Subscription.create stripe.Subscription.create, stripe_customer.id represents the ID of the customer in Stripe's system li créenah lfog, items=[{'plan': plan}]: This parameter specifies the items included in the subscription(²the ID yearly or monthly), Overall, this code snippet creates a new subscription in Stripe for a specific customer and associates it with a particular plan identified by its ID.
        customer = Customer() #This line creates a new instance of the Customer model
        customer.user = request.user #le nom ta3 user li bih togna nedekhlo lel admin page
        customer.stripeid = stripe_customer.id #specifies the customer ID for whom the subscription will be created
        customer.membership = True # indicates that the customer has a membership.
        customer.cancel_at_period_end = False #je pense its indicating that the subscription should not be canceled at the end of the billing period.
        customer.stripe_subscription_id = subscription.id #id ta3 subscription
        customer.save() # This saves the customer instance to the database with the customer's information.
        return redirect('home')
    else : # hna rana fl method == GET ye3ni fl fenetre ta3 li dekhel fiha redeem
        plan = 'monthly' #ki tedkhol lel lien ta3 checkout te3tik par défault monthly
        coupon = 'none'  #est un ticket papier offrant une réduction en valeur ou en pourcentage sur l'achat d'un produit (9assimet chira2)
        price = 1000  #the price of the product, 1000 pennies is 10 bucks(dollars) nekhedmo bl pennies bach ntigo ne7esbo mor lfassila
        og_dollar = 10  #the original price
        coupon_dollar = 0 #9assimet chira2 bl dollar machi pennies
        final_dollar = 10 # hadi tmetel lprix finale drnah par défault 10 par exmpl en cas ykon 3ndna coupon yeswa 5$ ne9so 10 mn 5 ta3 coupon tsama tweli 5 tsama le prix finale 5
        if request.method == 'GET' and 'plan' in request.GET : #psq fl checkout.html rana dayrin get fl <form> and 'plan' in request.GET checks if the parameter named 'plan' li rahi fl la fonction plan exists in the query parameters of the request
            if request.GET['plan'] == 'yearly' : #yla clickina sur yearly psq fl join.html 3ndna lien {% url 'checkout' %}?plan=yearly"
                plan = 'yearly'
                price = 10000
                og_dollar = 100
                final_dollar = 100
        if request.method == 'GET' and 'coupon' in request.GET : #yla user dakhel fl input ta3 promo code(redeem)
            if request.GET['coupon'].lower() in coupons : #yla code promo hada mewjod fl coupons(halloween wla welcome) 
                coupon = request.GET['coupon'].lower() # coupon yedi halloween wla welcome en miniscule
                percentage = coupons[coupon]  #percentage yedi la valeur ta3 halloween wla welcome ye3ni 31 wla 10
                coupon_price = int((percentage/100) * price) #coupon_price représente la valeur ta3 9assimet chira2 bl pennies 
                price = price - coupon_price #price howa la valeur total ta3 chhal ykheles user be3d ma fe3el code promo mais rahi en pennies
                coupon_dollar = str(coupon_price)[:-2] + '.' + str(coupon_price)[-2:] #bhadi hawelna la valeur ta3 9assimet chira2 mn pennies lel dollar [:-2] te3tina ga3 ar9am à part zoj twala '.' représente la vergule [-2:] représente ghi 2 ar9am twala par exmpl ykon 3ndna coupon_price = 300 [:-2] becomes '3' and [-2:] becomes '00' The final value of coupon_dollar is '3.00'.  
                final_dollar = str(price)[:-2] + '.' + str(price)[-2:] #hawelna la valeur total mn pennies lel dollar
        return render(request, 'plans/checkout.html', {'plan':plan, 'coupon':coupon, 'price':price, 'og_dollar':og_dollar, 'coupon_dollar':coupon_dollar, 'final_dollar':final_dollar})

def settings(request):
    membership = False
    cancel_at_period_end = False
    if request.method == 'POST' : #hadi m3a talya ki ydekhel user les infos ta3 la carte bancaire ta3k w ydir submit
        subscription = stripe.Subscription.retrieve(request.user.customer.stripe_subscription_id) #create current subscription with stripe, is using the Stripe API to retrieve the details of a subscription associated with a user's customer object. The retrieved subscription ydir bzf swaleh like updating the subscription, canceling it, or retrieving information about the subscription status, plan
        subscription.cancel_at_period_end = True #modify specific attributes of objects (subscription or customer) to indicate that a subscription should be canceled at the end of the current billing period
        request.user.customer.cancel_at_period_end = True #modify specific attributes of objects (subscription or customer) to indicate that a subscription should be canceled at the end of the current billing period
        cancel_at_period_end = True
        subscription.save()
        request.user.customer.save()
        #n the first instruction, subscription.save(), you are saving changes made to the subscription object itself. In the second instruction, request.user.customer.save(), you are saving changes made to the customer object associated with the authenticated user.
    else :
        try :
            if request.user.customer.membership : #yla currently user li dar login membership ta3h True
                membership = True
            if request.user.customer.cancel_at_period_end : #yla currently user li dar login cancel_at_period_end ta3h True
                cancel_at_period_end = True
        except Customer.DoesNotExist : 
            membership = False
    return render(request, 'registration/settings.html', {'membership': membership, 'cancel_at_period_end' : cancel_at_period_end})

class SignUp(generic.CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        valid = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid


