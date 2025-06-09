from django.shortcuts import render
import jwt
import datetime
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import EmailMessage
from django.template import loader
from . import constants
from authentication.models import (UserDetails)
from datetime import datetime, timedelta, timezone
from django.contrib.auth.hashers import make_password
from django.conf import settings
from .permissions import CustomPermission



class Login(APIView):
    permission_classes = (CustomPermission,)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            },
            required=['email', 'password'],
        ),
        responses={
            200: openapi.Response(description='Login successful', schema=openapi.Schema
                (
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token'),
                        'userId': openapi.Schema(type=openapi.TYPE_STRING, description='User ID'),
                    }
                )
            ),
            400: openapi.Response('Invalid credentials or request body.'),
            401: openapi.Response('Unauthorized.'),
            500: openapi.Response('Internal Server Error'),
        }
    )

        
    def post(self, request):
        data = self.request.data
        email = data[EMAIL]
        email = email.lower()
        password = data[PASSWORD]
        user = UserDetails.objects.filter(email=email).values()

        if user.exists():
            user = user.first()
            if user[Constants.BLOCKED] == True:
                return Response({Constants.JSON_MESSAGE: "The user has been deactivated, Please contact the administrator"}, status=status.HTTP_403_FORBIDDEN)
            user_password = user[Constants.ENCRYPTED_PASSWORD]
            if password == user_password:
                payload = {
                    USER_ID: user[USER_ID],
                    ROLE: user[ROLE],
                    EXPIRY_TIME: str(datetime.datetime.utcnow() + datetime.timedelta(minutes=60)),
                    "creationTime": str(datetime.datetime.utcnow()),
                }
                secretKey = Constants.SECRET_KEY
                loginToken = jwt.encode(payload, secretKey, algorithm='HS256')
                response = Response({
                    EMAIL: user[EMAIL],
                    ROLE: user[ROLE],
                    FIRST_NAME: user[FIRST_NAME],
                    LAST_NAME: user[LAST_NAME],
                    "phone": user[PHONE_NUMBER],
                    "token": loginToken
                },
                    status=status.HTTP_200_OK
                )
                return response
            else:
                return Response({Constants.JSON_MESSAGE: "Invalid Password. Try Again"},
                                status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({Constants.JSON_MESSAGE: "Invalid Credentials. Try Again"},
                            status=status.HTTP_401_UNAUTHORIZED)




class SignUp(APIView):
    permission_classes = (CustomPermission,)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'fullName': openapi.Schema(type=openapi.TYPE_STRING),
                # add other fields if any
            },
            required=['email', 'password', 'fullName'],
        ),
        responses={
            201: openapi.Response(
                description='User successfully created',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'userId': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response('Bad request, user already exists or invalid data.'),
            500: openapi.Response('Internal Server Error'),
        }
    )


    def post(self,request):
        try:
            data = self.request.data
            email = data[EMAIL]
            email = email.lower()
            encryptedPassword = data[PASSWORD]
            first_name = data[FIRST_NAME]
            last_name = data[LAST_NAME]
            phone_number = data[PHONE_NUMBER]

            if not all([email, password, first_name, last_name]):
                return Response(
                    {Constants.JSON_MESSAGE: "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            

            if UserDetails.objects.filter(email=email).exists():
                return Response(
                    {Constants.JSON_MESSAGE: "Email already registered"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            hashed_password = make_password(password)

            user = UserDetails.objects.create(
                email=data[EMAIL].lower(),
                encryptedPassword=make_password(data[PASSWORD]),
                firstName=data[FIRST_NAME],
                lastName=data[LAST_NAME],
                phoneNumber=data.get(PHONE_NUMBER, ""),
                blocked=False,
                role=USER 
            )

            expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
            payload = {
                USER_ID: user.id,
                EMAIL: user.email,
                EXPIRY_TIME: str(datetime.datetime.utcnow() + datetime.timedelta(minutes=60)),
            }
            secret_key = Constants.SECRET_KEY
            token = jwt.encode(payload, secret_key, algorithm='HS256')

            return Response(
                {
                    Constants.JSON_MESSAGE: "Account created successfully",
                    'userId': user.userId,
                    'email': user.email,
                    'firstName': user.firstName,
                    'lastName': user.lastName,
                    'message': "Account created successfully",
                    'token': token
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {Constants.JSON_MESSAGE: f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResetPassword(APIView):
    permission_classes = [AllowAny]
    

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            },
            required=['password'],
        ),
        responses={
            200: 'Password reset successful',
            400: 'Invalid token',
        }
    )


    def post(self, request):
        try:
            requestUserToken = request.headers[Constants.TOKEN_HEADER]
            try:
                requestUserId = IdExtraction(requestUserToken)
                if isinstance(requestUserId, Exception):
                    raise Exception(Constants.INVALID_TOKEN_MESSAGE)
            except Exception as e:
                return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_403_FORBIDDEN)
            data = request.data
            password = data[PASSWORD]
            user = UserDetails.objects.filter(userId=requestUserId).first()
            user.encryptedPassword = password
            user.save()
            return Response({Constants.JSON_MESSAGE: Constants.SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def secondsToMinutes(time):
    minutes = time // 60
    seconds = time % 60
    return str(minutes) + " minutes and " + str(seconds) + " seconds"


def IdExtraction(token):
    try:
        secretKey = Constants.SECRET_KEY
        payload = jwt.decode(token, secretKey, algorithms=['HS256'])
        userId = payload[USER_ID]
        return userId
    except Exception as e:
        return e


def ConvertToString(questionJson):
    numbers = questionJson['numbers']
    operator = questionJson['operator']
    if operator == '*' or operator == '/':
        return str(numbers[0]) + operator + str(numbers[1])
    else:
        question = str(numbers[0])
        for i in range(1, len(numbers)):
            if numbers[i] > 0:
                question += (operator + str(numbers[i]))
            else:
                question += str(numbers[i])

        return question





class ForgotPassword(APIView):
    permission_classes = (CustomPermission,)
    

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    format='email',
                    example="user@example.com"
                ),
            },
            required=['email'],
        ),
        responses={
            200: openapi.Response(
                description="Password reset link sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Reset link sent to email"
                        ),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid email address"
                        ),
                    }
                )
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="User not found"
                        ),
                    }
                )
            ),
        },
       operation_summary="Request password reset",
       operation_description="Send password reset link to user's email",
    )
    def post(self, request):
        try:
            request_data = request.data
            email = request_data[EMAIL]
            if email is None:
                return Response({Constants.JSON_MESSAGE: "Invalid email Id"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()

            if user is None:
                return Response({Constants.JSON_MESSAGE: "Invalid email Id"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate access token with 60 minutes expiry
            expiry_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            payload = {
                     EMAIL: user.email,
                     EXPIRY_TIME: expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            }

            secrect_key = settings.SECRET_KEY
            access_token = jwt.encode(payload, secrect_key, algorithm='HS256')

            link = Constants.FORGOT_PASSWORD_LINK + access_token
            
            return sendEmail(email, "Password Reset Link active only for 15 mins", link)

        except Exception as e:
            return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  



class ResetPasswordV2(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Reset user password",
        operation_description="Reset password using valid token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Password reset token"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='password',
                    description="New password"
                ),
            },
            required=['token', 'password'],
        ),
        responses={
            200: openapi.Response(
                description="Password reset successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Password updated successfully"
                        ),
                    }
                )
            ),
            400: openapi.Response(description="Invalid or expired token"),
            500: openapi.Response(description="Internal server error"),
        }
    )


    def post(self, request):
        try:
            data = request.data
            requestUserToken = data['token']
            if not checkExpiry(requestUserToken):
                return Response({Constants.JSON_MESSAGE: "Token has Expired."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                requestUserId = IdExtraction(requestUserToken)
                if isinstance(requestUserId, Exception):
                    raise Exception(Constants.INVALID_TOKEN_MESSAGE)
            except Exception as e:
                return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_403_FORBIDDEN)
            password = data[PASSWORD]
            user = UserDetails.objects.filter(userId=requestUserId).first()
            user.encryptedPassword = password
            user.save()
            return Response({Constants.JSON_MESSAGE: Constants.SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def checkExpiry(token):
    try:
        secretKey = Constants.SECRET_KEY
        payload = jwt.decode(token, secretKey, algorithms=['HS256'])
        expiryTime = payload[Constants.EXPIRY_TIME].split(".")[0]
        convertedExpiryTime = datetime.datetime.strptime(expiryTime, "%Y-%m-%d %H:%M:%S")
        if convertedExpiryTime < datetime.datetime.utcnow():
            return False
        return True
    except Exception as e:
        return e


def sendLinkEmail(token, userName, emailId):
    url = "core.com/resetPassword/v2/" + token
    content = {
        'url': url,
        "name": userName
    }
    template = loader.get_template('ForgotPasswordTemplate.html').render(content)
    email = EmailMessage(
        "Link To change your Password",
        template,
        'gourivishnupriya29@gmail.com',
        [emailId]
    )
    email.content_subtype = 'html'
    result = email.send()
    return result