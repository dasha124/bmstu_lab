from django.utils import timezone
from django.db.models import Q
# Create your views here.
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from datetime import date
from django.db import connection
from django.http import JsonResponse

from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from list_of_diseases.serializers import *
from list_of_diseases.models import *
from rest_framework.decorators import api_view
from operator import itemgetter
# from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
import redis
import uuid
from .permissions import *
import json
from django.contrib.sessions.models import Session
from .jwt_tokens import *
from django.core.cache import cache

def get_session_id(request):
    session = request.COOKIES.get('session_id')
    if session is None:
        session = request.data.get('session_id')
    if session is None:
        authorization_header = request.headers.get("Authorization")
        if authorization_header and authorization_header.lower().startswith("bearer "):
            session = authorization_header[len("bearer "):]
        else:
            session = authorization_header
    return session



# @swagger_auto_schema(request_body=UserLoginSerializer)
# @permission_classes([AllowAny])
# @authentication_classes([])
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def register(request):
    # Ensure username and passwords are posted is properly
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = serializer.save()
    message = {
        'message': 'Пользователь успешно зарегистрирован',
        'user_id': user.id
    }

    return Response(message, status=status.HTTP_201_CREATED)
    


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    # Проверка входных данных
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        print(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Аутентификация пользователя
    user = authenticate(request, **serializer.validated_data)
    if user is None:
        message = {"message": "Пользователь не найден"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    # Создание токена доступа
    access_token = create_access_token(user.id)

    # Сохранение данных пользователя в кеше
    user_data = {
        "user_id": user.id,
        "user_name": user.username,
        "user_email": user.email,
        "is_superuser": user.is_superuser,
        "access_token": access_token
    }
    access_token_lifetime = settings.ACCESS_TOKEN_LIFETIME
    cache.set(access_token, user_data, access_token_lifetime)

    # Отправка ответа с данными пользователя и установкой куки
    response_data = {
        "user_id": user.id,
        "user_name": user.username,
        "user_email": user.email,
        "is_superuser": user.is_superuser,
        "access_token": access_token
    }
    response = Response(response_data, status=status.HTTP_201_CREATED)
    response.set_cookie('access_token', access_token, httponly=False, expires=access_token_lifetime, samesite=None, secure=True)

    return response
    

@api_view(["POST"])
@permission_classes([AllowAny])
def check(request):
    access_token = get_access_token(request)
    print("check = ", access_token)

    if access_token is None:
        message = {"message": "Token is not found"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    if not cache.has_key(access_token):
        message = {"message": "Token is not valid"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    user_data = cache.get(access_token)
    return Response(user_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def refresh(request):
    refresh_token = get_access_token(request)
    if not refresh_token:
        return Response({'error': 'Refresh token not provided'}, status=400)

    try:
        refresh_payload = get_jwt_payload(refresh_token)
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Refresh token has expired'}, status=401)
    except jwt.InvalidTokenError:
        return Response({'error': 'Invalid refresh token'}, status=401)

    user_id = refresh_payload.get('user_id')

    if not user_id:
        return Response({'error': 'Invalid refresh token'}, status=401)

    new_access_token = create_refresh_token(user_id)

    return Response({'access_token': new_access_token}, status=200)




# @swagger_auto_schema(method='post')
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
   
    access_token = get_access_token(request)
    print("logout = ", access_token)

    if access_token is None:
        message = {"message": "Token is not found in cookie"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    if cache.has_key(access_token):
        cache.delete(access_token)

    message = {"message": "Logged out successfully!"}
    response = Response(message, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')

    return response




# список заболеваний (услуг)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_diseases(request, format=None):
    print('get_1')
    disease_name_r = request.GET.get('disease_name')
    print('disease_name_r =', disease_name_r)
    diseases = Disease.objects.filter(status='a')

    access_token = get_access_token(request)
    print("get_diseases = ", access_token)

    if disease_name_r:
        diseases = Disease.objects.filter(
            Q(status='a') &
            Q(disease_name__icontains=disease_name_r.lower())
        )
        serializer = DiseaseSerializer(diseases, many=True )

        return Response(serializer.data)
    
    serializer = DiseaseSerializer(diseases, many=True )
    
    return Response(serializer.data)


# добавление нового заболевания (услуги)
@permission_classes([IsManager])
@api_view(['POST'])
def add_disease(request, format=None):

    serializer = DiseaseSerializer(data=request.data)

    if serializer.is_valid():

        serializer.save()
        diseases = Disease.objects.filter(status='a')
        serializer = DiseaseSerializer(diseases, many=True )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# информация о заболевании (услуге)
@api_view(['GET'])
def get_disease(request, id, format=None):
    print("disease_id =", id)
    disease = get_object_or_404(Disease, id=id)
    if request.method == 'GET':
        serializer = DiseaseSerializer(disease)
        return Response(serializer.data)
    


# обновление информации о заболевании (услуге)
# @swagger_auto_schema(method='put', request_body=DiseaseSerializer)
#  !! @permission_classes([IsModerator])
@api_view(['PUT'])
def update_disease(request, id, format=None):
    disease = get_object_or_404(Disease, disease_id=id)
    serializer = DiseaseSerializer(disease, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление информации о заболевании (услуге)


@api_view(['DELETE'])
@permission_classes([IsManager])
def delete_disease(request, id, format=None):
    print('delete')
    disease = get_object_or_404(Disease, id=id)
    disease.status="d"
    disease.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


# добавление услуги в заявку

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_disease_to_drug(request, id):

    if not Disease.objects.filter(id=id).exists():
        return Response(f"Заболевания с таким id не найдено")
    
    token = get_access_token(request)
    print("token =", token)
    
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('<div>пусто</div>')


    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    print("uuuuuuuuuser =", user_id)
    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)
    
    
    disease = Disease.objects.get(id=id)
    drug = Medical_drug.objects.filter(status=0).last()

    if drug is None:
        drug = Medical_drug.objects.create()
        print("POST add_disease_to_drug_ ID_USER=PK")
        drug.user_id_id = user_id
    
    drug.for_disease.add(disease)
    drug.save()

    serializer = DiseaseSerializer(drug.for_disease, many=True)
    return Response(serializer.data)
    



# список препаратов (заявок)

#  !! @permission_classes([IsModerator])
# @authentication_classes([SessionAuthentication, BasicAuthentication])

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_drugs(request, format=None):

    token = get_access_token(request)
    # Добавлен блок для обработки отсутствия токена, вам может потребоваться определить, как обрабатывать эту ситуацию
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('<div>пусто</div>')


    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    print("uuuuuuuuuser =", user_id)
    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)

    if not curr_user.is_superuser:
        drugs= Medical_drug.objects.exclude(status__in=[4, 0]).order_by('-time_create').filter(user_id_id=user_id)
    else:
        drugs= Medical_drug.objects.exclude(status__in=[4, 0]).order_by('-time_create')

    serializer = DrugSerializer(drugs, many=True)
    # print(serializer.data)

    return Response(serializer.data)



# информация о препарате (заявке)
#  !! @permission_classes([IsModerator])

@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_drug(request, id, format=None):
    drug = get_object_or_404(Medical_drug, id=id)
   
    if request.method == 'GET':
        serializer = DrugSerializer(drug)
        return Response(serializer.data)
    
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def create_drug(request, format=None):
    print("try creaaaaaaaate drug")

    token = get_access_token(request)
    # Добавлен блок для обработки отсутствия токена, вам может потребоваться определить, как обрабатывать эту ситуацию
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    print("uuuuuuuuuser =", user_id)
    curr_user = CustomUser.objects.get(id = user_id)
    # print("cccccccccccurrr uuser =", curr_user)
    
    drug = Medical_drug.objects.get(user_id_id=user_id, status=0)
    # print(drug.for_disease.get())
    serializer = DrugSerializer(drug, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


    
    # drug.for_disease.objects.get()
    
    # print("dd =", drugs)
    # serializer = DrugSerializer(drugs, many=True)
    # # print(serializer.data)

    return Response(serializer.data)


# изменение информации о препарате (заявке)
#  !! @permission_classes([IsModerator])
#  !! @authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(['PUT'])
def update_drug(request, id, format=None):
    drug = get_object_or_404(Medical_drug, drug_id=id)
    serializer = DrugSerializer(drug, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление препарата (заявки)
@api_view(['DELETE'])
@permission_classes([AllowAny])
@authentication_classes([])
def delete_drug(request, id, format=None):
    print('delete drug')
    drug = get_object_or_404(Medical_drug, id=id)
    drug.status=4
    drug.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

# ???????????? удаление препарата-черновика (заявки)
@permission_classes([IsAuthenticated])
@api_view(['DELETE'])
def delete_entered_drug(request, format=None):
    if not Medical_drug.objects.filter(status=0).exists():
        return Response(f"Препарата со статусом 'Черновик' не существует")
    
    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)

    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)
    
    
    entered_drugs = Medical_drug.objects.filter(status=0, user_id_id=user_id)
    for drug in entered_drugs:
        drug.status=4
        drug.save()
    serializer = DrugSerializer(entered_drugs, many=False)
    return Response(serializer.data)







@api_view(['PUT'])
@permission_classes([AllowAny])
@authentication_classes([])
def drug_update_status_user(request, id):


    print("___________drug_update_status_user")

    token = get_access_token(request)
    # Добавлен блок для обработки отсутствия токена, вам может потребоваться определить, как обрабатывать эту ситуацию
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    print("uuuuuuuuuser =", user_id)

    if not Medical_drug.objects.filter(id=id).exists():
        return Response(f"Препарата с таким id не существует")
    
    STATUSES = [0, 1, 2, 3, 4]
    request_st = request.data["status"]

    if request_st not in STATUSES:
        return Response("Статус не корректен")
    
    drug = Medical_drug.objects.get(id=id)
    drug_st = drug.status
    print("drug_st =", drug_st)

    if drug_st == 4:
        return Response("Изменение статуса невозможно")
    
    if request_st == 1:
        drug.status = request_st
        drug.save()

        serializer = DrugSerializer(drug, many=False)
        return Response(serializer.data)
    else:
        return Response("Изменение статуса невозможно")
    

    

#  !! @permission_classes([IsModerator])
#  !! @authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([])
def drug_update_status_admin(request, id):
    if not Medical_drug.objects.filter(id=id).exists():
        return Response(f"Препарата с таким id не существует")
    
    STATUSES = [0, 1, 2, 3, 4]
    request_st = request.data["status"]

    if request_st not in STATUSES:
        return Response("Статус не корректен")
    
    drug = Medical_drug.objects.get(id=id)
    drug_st = drug.status
    print("drug_st =", drug_st)

    if request_st == 2 or request_st == 3:
        drug.status = request_st
        drug.save()

        serializer = DrugSerializer(drug, many=False)
        return Response(serializer.data)
    else:
        return Response("Изменение статуса невозможно")
    

# удаление заболевания из связанного с ним препарата (из м-м)

#  !! @permission_classes([IsModerator])
#  !! @authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(['DELETE'])
def delete_disease_from_drug(request, disease_id_r, drug_id_r, format=None):
    print('delete')
    if not Disease.objects.filter(id=disease_id_r).exists():
        return Response(f"Заболевания с таким id не существует")
    if not Medical_drug.objects.filter(drug_id=drug_id_r).exists():
        return Response(f"Препарата с таким id не существует")
    
    
    disease = Disease.objects.get(id=disease_id_r)
    print("disease =", disease)
    drug = Medical_drug.objects.get(id=drug_id_r)
    print("drug =", drug)
    if drug.for_disease.exists():
        print("drug_disease type =", drug.for_disease.get())
        drug.for_disease.remove(disease)
        drug.save()

        return Response(f"Удаление выполнено")
    else:
        return Response(f"Объектов для удаления не найдено", status = status.HTTP_404_NOT_FOUND)



# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)




# @authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(['PUT'])
@permission_classes([AllowAny])
def async_result(request, format=None):
    try:
        # Преобразуем строку в объект Python JSON
        json_data = json.loads(request.body.decode('utf-8'))
        print(json_data)
        const_token = 'my_secret_token'

        if const_token != json_data['token']:
            return Response(data={'message': 'Ошибка, токен не соответствует'}, status=status.HTTP_403_FORBIDDEN)

        # Изменяем значение sequence_number
        try:
            # Выводит конкретную заявку создателя
            drug = get_object_or_404(Medical_drug, id=json_data['id_test'])
            drug.status = json_data['test_status']
            # Сохраняем объект Location
            drug.save()
            data_json = {
                'id': drug.id,
                'test_status': drug.get_test_status_display_word(),
                'status': drug.get_grug_display_word()
            }
            return Response(data={'message': 'Статус тестированя успешно обновлен', 'data': data_json},
                            status=status.HTTP_200_OK)
        except ValueError:
            return Response({'message': 'Недопустимый формат преобразования'}, status=status.HTTP_400_BAD_REQUEST)
    except json.JSONDecodeError as e:
        print(f'Error decoding JSON: {e}')
        return Response(data={'message': 'Ошибка декодирования JSON'}, status=status.HTTP_400_BAD_REQUEST)
    
