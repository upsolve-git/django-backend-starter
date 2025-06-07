# backend
# django-backend-starter

django-backend-starter is a django appliaction which acts as a base for every project . it includes features for login, sign up, reset passwordand forgot password.

## project structure

The project consists of foloowing django apps:
 
- core
-authentication

## setup

### prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1.Clone the repository:
  ...
  https://github.com/upsolve-git/django-backend-starter.git

  cd core
  ....


2. Create and activate a virtual environment:Add commentMore actions
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:Add commentMore actions
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:Add commentMore actions
   Create a `.env` file in the project root and add the following variables:
   ...
                                            .env
   DB_NAME=_db_name
   DB_USER=_db_username
   DB_PASSWORD=_db_password
   DB_HOST=_db_host
   DB_PORT=_db_port
   SECRET_KEY=your_secret_key

5. Run database migrations:
   ```
   python manage.py migrate
   ```
   
6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

The application should now be running at `http://localhost:8000`.

## authentication


The project supports multiple authentication methods:
-Login
-Sign Up
-Reset Password
-Forgot Password

Refer to the `authentication/views.py` file for implementation details.


For detailed API documentation, refer to the individual app's `urls.py` and `views.py` files.

## Contributing
1. Fork the repositoryAdd commentMore actions
2. Create your feature branch (`git checkout -b feature/YourFeatureName`)
3. Commit your changes (`git commit -m 'Add some YourFeatureName'`)
4. Push to the branch (`git push origin feature/YourFeatureName`)
5. Open a Pull Request