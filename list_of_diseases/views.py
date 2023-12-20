from django.utils import timezone
from django.db.models import Q
# Create your views here.
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from datetime import date
from django.db import connection

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
from .permissions import IsAuthenticated, IsModerator
import json




# список заболеваний (услуг)
@api_view(['GET'])
@permission_classes([AllowAny])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
def get_diseases(request, format=None):
    print('get_1')
    disease_name_r = request.GET.get('disease_name')
    print('disease_name_r =', disease_name_r)
    diseases = Disease.objects.filter(status='a')

    if disease_name_r:
        diseases = Disease.objects.filter(
            Q(status='a') &
            Q(disease_name__icontains=disease_name_r.lower())
        )
        serializer = DiseaseSerializer(diseases, many=True )

        return Response(serializer.data)
    
    serializer = DiseaseSerializer(diseases, many=True )
    serialized_data = serializer.data


    return Response(serializer.data)


# список заболеваний (услуг) с фильтром поиска 
@api_view(['GET'])
def get_found_diseases(request, format=None):
    print('get')
    disease_name_r = request.data.get('disease_name')
    sphere_r = request.data.get('sphere')
    print("disease_name_r =", disease_name_r, sphere_r)

    diseases = Disease.objects.filter(status='a')

    if disease_name_r:
        diseases = diseases.filter(disease_name=disease_name_r)
        serializer = DiseaseSerializer(diseases, many=True )
   
        return Response(serializer.data)

    if sphere_r:
        spheres = Sphere.objects.get(sphere_name=sphere_r)
        diseases = diseases.filter(sphere_id=spheres.sphere_id)
        serializer = DiseaseSerializer(diseases, many=True )
   
        return Response(serializer.data)




# добавление нового заболевания (услуги)
@api_view(['POST'])
@permission_classes([IsModerator])
def post_disease(request, format=None):

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
@permission_classes([IsModerator])
@api_view(['PUT'])
def put_disease(request, id, format=None):
    disease = get_object_or_404(Disease, disease_id=id)
    serializer = DiseaseSerializer(disease, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление информации о заболевании (услуге)
@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def delete_disease(request, id, format=None):
    print('delete')
    disease = get_object_or_404(Disease, disease_id=id)
    disease.status='d'
    disease.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


# добавление услуги в заявку
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_disease_to_drug(request, id):

    if not Disease.objects.filter(disease_id=id).exists():
        return Response(f"Заболевания с таким id не найдено")
    
    ssid = request.COOKIES.get("session_id")
    user = CustomUser.objects.get(username=session_storage.get(ssid).decode('utf-8'))
    
    
    disease = Disease.objects.get(disease_id=id)
    drug = Medical_drug.objects.filter(status='e').last()

    if drug is None:
        drug = Medical_drug.objects.create()
        print("POST add_disease_to_drug_ ID_USER=PK")
        drug.user_id = user.pk
    
    drug.for_disease.add(disease)
    drug.save()

    serializer = DiseaseSerializer(drug.for_disease, many=True)
    return Response(serializer.data)
    

# список препаратов (заявок)
@api_view(['GET'])
@permission_classes([IsModerator])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_drugs(request, format=None):

    drugs= Medical_drug.objects.exclude(status__in=['d', 'e']).order_by('-time_create')
    #drugs= Medical_drug.objects.all()
    serializer = DrugSerializer(drugs, many=True)

    return Response(serializer.data)

    

# информация о препарате (заявке)
@api_view(['GET'])
@permission_classes([IsModerator])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_drug(request, id, format=None):
    drug = get_object_or_404(Medical_drug, drug_id=id)

    if request.method == 'GET':
        serializer = DrugSerializer(drug)
        return Response(serializer.data)
    

# изменение информации о препарате (заявке)
@api_view(['PUT'])
@permission_classes([IsModerator])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def update_drug(request, id, format=None):
    drug = get_object_or_404(Medical_drug, drug_id=id)
    serializer = DrugSerializer(drug, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление информации о препарате (заявке)
@api_view(['DELETE'])
@permission_classes([IsModerator])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def delete_drug(request, id, format=None):
    print('delete')
    drug = get_object_or_404(Medical_drug, drug_id=id)
    drug.status='d'
    drug.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

# удаление введенного препарата (заявки)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_entered_drug(request, format=None):
    if not Medical_drug.objects.filter(status='e').exists():
        return Response(f"Препарата со статусом 'Черновик' не существует")
    
    entered_drugs = Medical_drug.objects.filter(status='e')
    for drug in entered_drugs:
        drug.delete()
    serializer = DrugSerializer(entered_drugs, many=False)
    return Response(serializer.data)





@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def drug_update_status_user(request, id):
    if not Medical_drug.objects.filter(drug_id=id).exists():
        return Response(f"Препарата с таким id не существует")
    
    STATUSES = ['e', 'o', 'f', 'c', 'd']
    request_st = request.data["status"]

    if request_st not in STATUSES:
        return Response("Статус не корректен")
    
    drug = Medical_drug.objects.get(drug_id=id)
    drug_st = drug.status
    print("drug_st =", drug_st)

    if drug_st == 'd':
        return Response("Изменение статуса невозможно")
    
    if request_st == 'd':
        drug.status = request_st
        drug.save()

        serializer = DrugSerializer(drug, many=False)
        return Response(serializer.data)
    else:
        return Response("Изменение статуса невозможно")
    

    
@api_view(['PUT'])
@permission_classes([IsModerator])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def drug_update_status_admin(request, id):
    if not Medical_drug.objects.filter(drug_id=id).exists():
        return Response(f"Препарата с таким id не существует")
    
    STATUSES = ['e', 'o', 'f', 'c', 'd']
    request_st = request.data["status"]

    if request_st not in STATUSES:
        return Response("Статус не корректен")
    
    drug = Medical_drug.objects.get(drug_id=id)
    drug_st = drug.status
    print("drug_st =", drug_st)

    if request_st == 'f' or request_st == 'c':
        drug.status = request_st
        drug.save()

        serializer = DrugSerializer(drug, many=False)
        return Response(serializer.data)
    else:
        return Response("Изменение статуса невозможно")
    

# удаление заболевания из связанного с ним препарата (из м-м)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def delete_disease_from_drug(request, disease_id_r, drug_id_r, format=None):
    print('delete')
    if not Disease.objects.filter(disease_id=disease_id_r).exists():
        return Response(f"Заболевания с таким id не существует")
    if not Medical_drug.objects.filter(drug_id=drug_id_r).exists():
        return Response(f"Препарата с таким id не существует")
    
    
    disease = Disease.objects.get(disease_id=disease_id_r)
    print("disease =", disease)
    drug = Medical_drug.objects.get(drug_id=drug_id_r)
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


# @swagger_auto_schema(request_body=UserLoginSerializer)
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
    


# @swagger_auto_schema(request_body=UserLoginSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):

    print('Looooooogin')

    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    # Аутентификация пользователя
    user = authenticate(request, **serializer.data)
    print(serializer.validated_data)
    print(user)
    
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, user.username)

        data = {
            "session_id": random_key,
            "user_id": user.id,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "username": user.username
        }

        response = Response(data, status=status.HTTP_201_CREATED)
        response.set_cookie("session_id", random_key, httponly=False)

        return response
    else:
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
    

# @swagger_auto_schema(method='post')
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    ssid = request.COOKIES.get("session_id")

    if ssid is None:
        return Response(status=status.HTTP_403_FORBIDDEN)

    session_storage.delete(ssid)

    logout(request._request)
    response = HttpResponse(status=status.HTTP_200_OK)
    response.delete_cookie("session_id")
    return response



@api_view(['PUT'])
@permission_classes([AllowAny])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def async_result(request, format=None):
    print('[INFO] API PUT [PUT_async_result]')
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
            return Response(data={'message': 'Статус миссии успешно обновлен', 'data': data_json},
                            status=status.HTTP_200_OK)
        except ValueError:
            return Response({'message': 'Недопустимый формат преобразования'}, status=status.HTTP_400_BAD_REQUEST)
    except json.JSONDecodeError as e:
        print(f'Error decoding JSON: {e}')
        return Response(data={'message': 'Ошибка декодирования JSON'}, status=status.HTTP_400_BAD_REQUEST)