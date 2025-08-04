# NEW CODE HERE
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Guest House API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f7f9fc;
                color: #333;
                text-align: center;
                padding: 50px;
            }
            h1 {
                color: #2c3e50;
            }
            .section {
                margin-top: 30px;
            }
            footer {
                margin-top: 60px;
                font-size: 0.9em;
                color: #888;
            }
            .btn {
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                font-size: 1em;
                color: white;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            .btn:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>👋 Welcome to the Guest House Management API</h1>
        <div class="section">
            <p>This platform powers the operations of our Guest House system.</p>
            <a href="/api/" class="btn">Go to API Endpoints</a>
            <a href="/admin/" class="btn">Go to Admin Panel</a>
        </div>
        <footer>
            Designed by <strong>Pacifique NSHIMIYIMANA</strong><br>
            <br>
            Student Reference Number: <strong>224021048</strong>
        </footer>
    </body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('guest_house.urls')),
    path('', home),
]
