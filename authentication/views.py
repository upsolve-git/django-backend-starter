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
from authentication.models import (UserDetails,OrganizationTag)
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
            200: openapi.Response(
                description='Login successful',
                schema=openapi.Schema(
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


    def get(self, request):
        return Response({
            "message": "Login endpoint",
            "required_fields": ["email", "password"],
            "method": "POST",
            "endpoint": request.build_absolute_uri()
        })
        
    def post(self, request):
        data = self.request.data
        email = data[Constants.EMAIL]
        email = email.lower()
        password = data[Constants.PASSWORD]
        user = UserDetails.objects.filter(email=email).values()

        if user.exists():
            user = user.first()
            if user[Constants.BLOCKED] == True:
                return Response({Constants.JSON_MESSAGE: "The user has been deactivated, Please contact the administrator"}, status=status.HTTP_403_FORBIDDEN)
            user_password = user[Constants.ENCRYPTED_PASSWORD]
            if password == user_password:
                organization = OrganizationTag.objects.filter(tagId=user["tag_id"]).first()
                organizationExpirationDate = organization.expirationDate
                if organizationExpirationDate < datetime.date.today():
                    return Response({Constants.JSON_MESSAGE: "The subscription has expired. Please contact the "
                                                             "administrator to renew it."},
                                    status=status.HTTP_403_FORBIDDEN)
                payload = {
                    Constants.USER_ID: user[Constants.USER_ID],
                    Constants.ROLE: user[Constants.ROLE],
                    Constants.EXPIRY_TIME: str(datetime.datetime.utcnow() + datetime.timedelta(minutes=60)),
                    "creationTime": str(datetime.datetime.utcnow()),
                    Constants.ORGANIZATION_EXPIRATION_DATE: str(organizationExpirationDate)
                }
                secretKey = Constants.SECRET_KEY
                loginToken = jwt.encode(payload, secretKey, algorithm='HS256')
                response = Response({
                    Constants.EMAIL: user[Constants.EMAIL],
                    Constants.ROLE: user[Constants.ROLE],
                    Constants.FIRST_NAME: user[Constants.FIRST_NAME],
                    Constants.LAST_NAME: user[Constants.LAST_NAME],
                    "phone": user[Constants.PHONE_NUMBER],
                    Constants.ORGANIZATION_NAME: organization.organizationName,
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
            email = data[Constants.EMAIL]
            email = email.lower()
            encryptedPassword = data[Constants.PASSWORD]
            first_name = data[Constants.FIRST_NAME]
            last_name = data[Constants.LAST_NAME]
            phone_number = data[Constants.PHONE_NUMBER]

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
                email=email,
                encryptedPassword=hashed_password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                blocked=False,  
                role="user",  
            )

            expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
            payload = {
                Constants.USER_ID: user.id,
                Constants.EMAIL: user.email,
                Constants.EXPIRY_TIME: str(datetime.datetime.utcnow() + datetime.timedelta(minutes=60)),
            }
            secret_key = Constants.SECRET_KEY
            token = jwt.encode(payload, secret_key, algorithm='HS256')

            return Response(
                {
                    Constants.JSON_MESSAGE: "Account created successfully",
                    Constants.EMAIL: user.email,
                    Constants.FIRST_NAME: user.first_name,
                    Constants.LAST_NAME: user.last_name,
                    "token": token 
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
            password = data[Constants.PASSWORD]
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
        userId = payload[Constants.USER_ID]
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

    def post(self, request):
        try:
            request_data = request.data
            email = request_data['email']
            if email is None:
                return Response({Constants.JSON_MESSAGE: "Invalid email Id"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()

            if user is None:
                return Response({Constants.JSON_MESSAGE: "Invalid email Id"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate access token with 60 minutes expiry
            expiry_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            payload = {
                Constants.EMAIL: user.email,
                Constants.EXPIRY_TIME: expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            }

            secrect_key = settings.SECRET_KEY
            access_token = jwt.encode(payload, secrect_key, algorithm='HS256')

            link = Constants.FORGOT_PASSWORD_LINK + access_token
            
            return sendEmail(email, "Password Reset Link active only for 15 mins", link)

        except Exception as e:
            return Response({Constants.JSON_MESSAGE: repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  



    def post(self, request):
        try:
            data = request.data
            email = data[Constants.EMAIL].lower()
            user = UserDetails.objects.filter(email=email).first()
            if user is not None:

                organization = OrganizationTag.objects.filter(tagId=user.tag_id).first()
                organizationExpirationDate = organization.expirationDate
                payload = {
                    Constants.USER_ID: user.userId,
                    Constants.ROLE: user.role,
                    Constants.EXPIRY_TIME: str(datetime.datetime.utcnow() + datetime.timedelta(minutes=60)),
                    "creationTime": str(datetime.datetime.utcnow()),
                    Constants.ORGANIZATION_EXPIRATION_DATE: str(organizationExpirationDate)

                }
                secretKey = Constants.SECRET_KEY
                loginToken = jwt.encode(payload, secretKey, algorithm='HS256')
                userName = user.firstName + " " + user.lastName
                sendLinkEmail(loginToken, userName, email)
                return Response({Constants.JSON_MESSAGE: Constants.SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
            else:
                return Response({Constants.JSON_MESSAGE: "The user doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({Constants.JSON_MESSAGE: repr(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ResetPasswordV2(APIView):
    permission_classes = [AllowAny]

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
            password = data[Constants.PASSWORD]
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