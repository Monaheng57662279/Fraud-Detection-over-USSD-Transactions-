import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, load_fraud_detection_model, load_label_encoders, UploadCSV, RealTime
from .forms import SingleTransactionForm, MultipleTransactionForm, CSVUploadForm, LoginForm
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils.timezone import make_aware
from datetime import datetime
import pytz
import re
import json
import pickle
from django.core.cache import cache
# from .retrieve_data import retrieve_data

 
def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

def predictions(request):
    return render(request, '/home/monaheng/Desktop/myproject/myproject/templates/predictions.html')


import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                # Handle non-CSV file uploads
                return render(request, 'upload_csv.html', {'form': form, 'error_message': 'Please upload a CSV file.'})
            
            try:
                # Read CSV data into a Pandas DataFrame
                df = pd.read_csv(csv_file)

                logger.info(f"Number of rows in CSV: {len(df)}")

                # Iterate through DataFrame rows and create Transaction objects
                success_count = 0  # Track the number of successful creations
                for index, row in df.iterrows():
                    # Check for empty values before creating Transaction object
                    if not pd.isna(row['unix_time']) and row['unix_time'] != '':
                        try:
                            Transaction.objects.create(
                                contact_num=row['contact_num'],
                                merchant=row['merchant'],
                                category=row['category'],
                                amt=row['amt'],
                                unix_time=row['unix_time'],
                                is_fraud=row['is_fraud'],
                                trans_datetime=row['trans_datetime'],
                            )
                            success_count += 1
                        except Exception as e:
                            logger.error(f"Error creating Transaction: {e}")
                    else:
                        logger.warning(f"Skipping row with empty unix_time at index {index}")

                logger.info(f"Number of successful creations: {success_count}")

                return redirect('transaction_detail')  # Redirect to a success page
            except Exception as e:
                # Handle any exceptions during CSV processing
                logger.error(f"Error processing CSV file: {e}")
                return render(request, 'upload_csv.html', {'form': form, 'error_message': f'Error processing CSV file: {e}'})
    else:
        form = CSVUploadForm()

    return render(request, 'upload_csv.html', {'form': form})


def transaction_detail(request):
    transactions = Transaction.objects.all().order_by('-amt')  # Order by recent first
    fraud_count = transactions.filter(is_fraud=True).count()
    total_transactions = transactions.count()
    fraud_percentage = (fraud_count / total_transactions) * 100 if total_transactions != 0 else 0

    # Paginate the transactions (show 20 per page)
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'page': page,
        'fraud_count': fraud_count,
        'total_transactions': total_transactions,
        'fraud_percentage': fraud_percentage,
    }
    return render(request, 'transaction_detail.html', context)

def predict_fraud_single(request):
    if request.method == 'POST':
        form = SingleTransactionForm(request.POST)
        if form.is_valid():
            try:
                # Load model and label encoders
                model = load_fraud_detection_model()
                label_encoders = load_label_encoders()

                # Extract cleaned data from form
                cleaned_data = form.cleaned_data
                contact_num = cleaned_data['contact_num']
                merchant = cleaned_data['merchant']
                category = cleaned_data['category']
                amt = cleaned_data['amt']
                unix_time = cleaned_data['unix_time']
                trans_datetime = cleaned_data['trans_datetime']

                # Convert trans_datetime to numerical features
                trans_datetime = pd.to_datetime(trans_datetime)
                month = trans_datetime.month
                day = trans_datetime.day
                hour = trans_datetime.hour
                minute = trans_datetime.minute

                # Handle unseen labels in categorical features
                merchant_encoded = label_encoders['merchant'].transform([merchant])[0] if merchant in label_encoders['merchant'].classes_ else -1
                category_encoded = label_encoders['category'].transform([category])[0] if category in label_encoders['category'].classes_ else -1

                # Check if all categorical features are valid
                if merchant_encoded == -1 or category_encoded == -1:
                    error_message = "Invalid categorical feature(s) detected."
                    return render(request, 'predict_fraud_single.html', {'error': error_message, 'single_form': form})

                # Prepare data for prediction
                encoded_data = pd.DataFrame({
                    'contact_num': [contact_num],
                    'merchant': [merchant_encoded],
                    'category': [category_encoded],
                    'amt': [amt],
                    'unix_time': [unix_time],
                    'month': [month],
                    'day': [day],
                    'hour': [hour],
                    'minute': [minute],
                })

                # Make prediction
                prediction = model.predict(encoded_data)[0]
                result_text = "Fraudulent" if prediction == 1 else "Legitimate"

                # Pass the result_text to the template for rendering
                return render(request, 'fraud_prediction_result.html', {'prediction': result_text})
            except FileNotFoundError:
                error_message = "Model or label encoders not found."
            except Exception as e:
                error_message = f"An error occurred during prediction: {e}"
                print(f"Error: {e}")
            return render(request, 'predict_fraud_single.html', {'error': error_message, 'single_form': form})
    else:
        single_form = SingleTransactionForm()
        return render(request, 'predict_fraud_single.html', {'single_form': single_form})



def normalize_datetime(date_str):
    # Example pattern for YYYY-MM-DD HH:MM:SS
    match = re.search(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
    # Add more patterns here for other expected formats
    return None  # Handle invalid formats

def predict_fraud_multiple(request):
    if request.method == 'POST':
        form = MultipleTransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Load the trained model and label encoders
                model = load_fraud_detection_model()
                label_encoders = load_label_encoders()

                csv_file = request.FILES['csv_file']
                df = pd.read_csv(csv_file)

                # Normalize 'trans_datetime' format
                df['trans_datetime'] = df['trans_datetime'].apply(normalize_datetime)

                # Ensure 'trans_datetime' is in the correct format and extract features
                try:
                    df['trans_datetime'] = pd.to_datetime(df['trans_datetime'], format='%Y-%m-%d %H:%M:%S')  # Adjust format as needed
                except pd.errors.ParserError:
                    error_message = "Incorrect date format in 'trans_datetime' column. Please use a valid format like YYYY-MM-DD HH:MM:SS."
                    return render(request, 'predict_fraud_multiple.html', {'error': error_message, 'csv_form': form})

                df['month'] = df['trans_datetime'].dt.month
                df['day'] = df['trans_datetime'].dt.day
                df['hour'] = df['trans_datetime'].dt.hour
                df['minute'] = df['trans_datetime'].dt.minute

                # Transform categorical features using label encoders
                for col in ['merchant', 'category']:
                    if col in label_encoders:
                        df[col] = label_encoders[col].transform(df[col].astype(str))

                # Select relevant features for prediction
                features = ['contact_num', 'merchant', 'category', 'amt', 'unix_time', 'month', 'day', 'hour', 'minute']
                X = df[features]

                # Make predictions
                predictions = model.predict(X)

                # Add predictions to the DataFrame
                df['is_fraud'] = predictions

                #Send email if any transaction is flagged as fraudulent
                if df['is_fraud'].any():
                    subject = 'Fraudulent Transaction Alert'
                    html_message = render_to_string('fraud_alert_email.html', {'transactions': df[df['is_fraud'] == 1]})
                    plain_message = strip_tags(html_message)
                    from_email = 'monahengmothabeng@gmail.com'
                    to_email = 'ostlerkoai@gmail.com'
                    send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
                if df['is_fraud'].any():
                    print("Fraudulent Transaction Alert:")
                    fraudulent_transactions = df[df['is_fraud'] == 1]
                    for index, transaction in fraudulent_transactions.iterrows():
                        print(f"Contact Number: {transaction['contact_num']}")
                        print(f"Merchant: {transaction['merchant']}")
                        print(f"Category: {transaction['category']}")
                        print(f"Amount: {transaction['amt']}")
                        print(f"Date and Time: {transaction['trans_datetime']}")
                        print("-" * 30)



                # Zip transactions with predictions and convert to list
                transactions_with_predictions = list(zip(df.to_dict('records'), predictions))

                # Paginate transactions for better display if needed
                paginator = Paginator(transactions_with_predictions, 10)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)

                # Pass transactions_with_predictions and other data to the template
                context = {'page_obj': page_obj}
                return render(request, 'fraud_prediction_results_multiple.html', context)
            except FileNotFoundError:
                error_message = "Model or label encoders not found."
            except Exception as e:
                error_message = "An error occurred during prediction."
                print(f"Error: {e}")
                return render(request, 'predict_fraud_multiple.html', {'error': error_message, 'csv_form': form})

    else:
        csv_form = MultipleTransactionForm()
        return render(request, 'predict_fraud_multiple.html', {'csv_form': csv_form})


def dashboard(request):
    # Retrieve user information (optional)
    user = request.user  # Assuming you have a user model

    # Context dictionary with your actual URLs
    context = {
        'upload_link': '/myapp/upload-csv/',
        'single_file_link': '/myapp/single_file/',
        'transaction_details': '/myapp/transactions/',
        'multiple_transaction': '/myapp/multiple_file/'
    }

    return render(request, 'dashboard.html', context)

from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page or home page
                return redirect('/')
            else:
                # Invalid username or password, handle accordingly
                # For example, you can add an error message to the form
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse('login'))

def go_to_other(request):
    return render(request, "fraud_prediction_result.html")


def create_transaction(request):
    if request.method == 'POST':
        # Process form data and create a new transaction
        new_transaction = Transaction.objects.create(
            contact_num=request.POST['contact_num'],
            merchant=request.POST['merchant'],
            category=request.POST['category'],
            amt=float(request.POST['amt']),
            unix_time=int(request.POST['unix_time']),
            trans_datetime=request.POST['trans_datetime']
        )
        # Retrieve data from Redis
        retrieved_data = new_transaction.retrieve_data()
        # Render a response or perform further actions
        return render(request, 'success.html', {'transaction': new_transaction, 'retrieved_data': retrieved_data})
    else:
        # Render the form for creating a new transaction
        return render(request, 'create_transaction.html')

def reports(request):
    # Retrieve all objects from the UploadCSV model
    all_data_files_objs = UploadCSV.objects.all()  # Use the correct model name here

    # Pass the objects to the template
    context = {'all_data_files_objs': all_data_files_objs}
    return render(request, 'file_reports.html', context)

# def delete_record(request, contact_num):
#     # Get the record based on the contact number
#     record = get_object_or_404(Transaction, contact_num=contact_num)
    
#     # Delete the record
#     record.delete()
    
#     # Redirect to a success page or another URL
#     return redirect('reports')  # Change 'success_page' to the appropriate URL

def delete_record(request, contact_num):
    if request.method == 'POST':
        # Get the record based on the contact number
        record = get_object_or_404(Transaction, contact_num=contact_num)
        
        # Check permissions or conditions if needed
        # Example: Only allow deletion by authenticated users
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to perform this action.")

        # Delete the record
        record.delete()
        
        # Redirect to a success page or another URL
        return redirect('reports')  # Change 'reports' to the appropriate URL
    else:
        # Handle GET requests or other methods if needed
        return HttpResponseForbidden("Invalid request method.")

# def predict_fraud_redis(request):
#     redis_conn = get_redis_connection("default")  # Connect to Redis
#     stream_name = "transactions_stream"  # Specify Redis stream name

#     # Read data from Redis stream
#     stream_data = redis_conn.xread({stream_name: ">"}, count=10)  # Read last 10 entries

#     # Load the fraud detection model and label encoders
#     with open('fraud_detection_model.pkl', 'rb') as f:
#         model, label_encoders = pickle.load(f)

#     # Process data for prediction and make predictions
#     predictions = []
#     for entry in stream_data[stream_name]:
#         transaction_data = json.loads(entry[1]['data'])

#         # Preprocess data and prepare features for prediction
#         df = pd.DataFrame([transaction_data])
#         for col in ['merchant', 'category']:
#             if col in label_encoders:
#                 df[col] = label_encoders[col].transform(df[col].astype(str))

#         # Make prediction using the loaded model
#         prediction = model.predict(df)[0]  # Assuming binary prediction
#         predictions.append({"id": transaction_data.get("id", ""),
#                             "is_fraud": bool(prediction)})

#     # Send response with predictions
#     return JsonResponse({"predictions": predictions})

# def get_data():
#     data = cache.get('my_data')
#     if data is None:
#         # Retrieve data from the database or another source
#         data = retrieve_data()
#         cache.set('my_data', data, timeout=3600)  # Cache for 1 hour
#     return data

def transaction_list(request):
    transactions = RealTime.objects.all()
    return render(request, 'transactions_list.html', {'transactions': transactions})


from django.shortcuts import render

def about_admin_dashboard(request):
    return render(request, 'about.html')